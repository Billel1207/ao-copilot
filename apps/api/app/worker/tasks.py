"""Tâches Celery asynchrones pour le pipeline IA."""
import io
import uuid

from app.config import settings
from app.database import SyncSessionLocal as SyncSession
from app.worker.celery_app import celery_app


def _set_progress(task_id: str, pct: int, step: str):
    """Stocke la progression dans Redis."""
    import redis as redis_lib
    r = redis_lib.from_url(settings.REDIS_URL)
    r.set(
        f"progress:{task_id}",
        f'{{"pct":{pct},"step":"{step}"}}',
        ex=3600,
    )


@celery_app.task(bind=True, name="process_document", max_retries=2, time_limit=300, soft_time_limit=280)
def process_document(self, doc_id: str):
    """Extraction texte + chunking + embeddings pour 1 document."""
    from app.models.document import AoDocument, DocumentPage
    from app.models.analysis import Chunk
    from app.services.pdf_extractor import extract_document
    from app.services.chunker import chunk_pages
    from app.services.embedder import embed_texts
    from app.services.storage import storage_service

    db = SyncSession()
    try:
        _set_progress(self.request.id, 5, "Téléchargement du fichier")
        doc = db.query(AoDocument).filter_by(id=uuid.UUID(doc_id)).first()
        if not doc:
            return {"error": "Document introuvable"}

        doc.status = "processing"
        db.commit()

        # Télécharger depuis S3
        _set_progress(self.request.id, 15, "Extraction du texte")
        pdf_bytes = storage_service.download_bytes(doc.s3_key)

        # Extraire texte selon le format du fichier (PDF, image, DOCX)
        pages = extract_document(pdf_bytes, doc.original_name)
        doc.page_count = len(pages)
        doc.has_text = any(p.char_count > 50 for p in pages)

        # Sauvegarder les pages (avec confiance OCR)
        for page in pages:
            dp = DocumentPage(
                document_id=doc.id,
                page_num=page.page_num,
                raw_text=page.raw_text,
                char_count=page.char_count,
                section=page.section,
                ocr_confidence=page.ocr_confidence,
            )
            db.add(dp)

        # Qualité OCR globale du document
        from app.services.pdf_extractor import compute_document_ocr_quality, detect_doc_type_from_content
        ocr_quality = compute_document_ocr_quality(pages)
        doc.ocr_quality_score = ocr_quality.get("ocr_score")
        doc.ocr_warning = ocr_quality.get("warning")

        # Détection type document par contenu si non identifié
        if doc.doc_type in (None, "AUTRES", ""):
            full_text = " ".join(p.raw_text for p in pages if p.raw_text)
            detected_type = detect_doc_type_from_content(full_text)
            if detected_type:
                import logging
                logging.getLogger(__name__).info(
                    "[%s] Type document détecté par contenu : %s → %s",
                    doc_id, doc.doc_type, detected_type,
                )
                doc.doc_type = detected_type

        db.flush()

        _set_progress(self.request.id, 40, "Découpage en chunks")
        pages_dicts = [{"page_num": p.page_num, "raw_text": p.raw_text} for p in pages]
        chunks = chunk_pages(pages_dicts, doc.original_name)

        _set_progress(self.request.id, 60, "Génération des embeddings")
        texts = [c.content for c in chunks]
        embeddings = embed_texts(texts)

        # Sauvegarder chunks + embeddings
        for chunk, embedding in zip(chunks, embeddings):
            ch = Chunk(
                document_id=doc.id,
                project_id=doc.project_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                token_count=chunk.token_count,
                embedding=embedding,
            )
            db.add(ch)

        doc.status = "done"
        db.commit()
        _set_progress(self.request.id, 100, "Document prêt")

        # Vérifier si tous les docs du projet sont done → lancer analyse
        _check_and_trigger_analysis(db, str(doc.project_id))

        return {"doc_id": doc_id, "pages": len(pages), "chunks": len(chunks)}

    except Exception as exc:
        db.rollback()
        doc = db.query(AoDocument).filter_by(id=uuid.UUID(doc_id)).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(exc)[:500]
            db.commit()
        # Guard : ne relancer que si le quota de retries n'est pas épuisé
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        raise exc  # Max retries atteint → Celery marque FAILURE
    finally:
        db.close()


def _check_and_trigger_analysis(db, project_id: str):
    """Lance l'analyse IA si tous les documents du projet sont traités."""
    from app.models.document import AoDocument
    docs = db.query(AoDocument).filter_by(project_id=uuid.UUID(project_id)).all()
    if all(d.status in ("done", "error") for d in docs) and any(d.status == "done" for d in docs):
        analyze_project.delay(project_id)


@celery_app.task(bind=True, name="analyze_project", max_retries=1, time_limit=1800, soft_time_limit=1740)
def analyze_project(self, project_id: str):
    """Pipeline IA complet 15 étapes : résumé, checklist, critères, Go/No-Go,
    timeline, CCAP, RC, AE, CCTP, DC, conflits, questions, scoring, cashflow."""
    from app.models.project import AoProject
    from app.services.analyzer import run_full_analysis

    db = SyncSession()
    try:
        project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
        if not project:
            return {"error": "Projet introuvable"}

        project.status = "analyzing"
        db.commit()

        _set_progress(self.request.id, 5, "Analyse complète en cours — 15 étapes")
        results = run_full_analysis(db, project_id)

        project.status = "ready"
        db.commit()

        _set_progress(self.request.id, 100, "Analyse terminée")

        # P2 — Notification email analyse terminée (fail silently)
        try:
            from app.models.user import User
            from app.models.analysis import ExtractionResult
            from app.services.email import send_analysis_complete
            creator = db.query(User).filter_by(id=project.created_by).first() if project.created_by else None
            if creator:
                summary_result = (
                    db.query(ExtractionResult)
                    .filter_by(project_id=project.id, result_type="summary")
                    .order_by(ExtractionResult.version.desc())
                    .first()
                )
                risk_count = 0
                action_count = 0
                if summary_result and summary_result.payload:
                    risk_count = len(summary_result.payload.get("risks", []))
                    action_count = len(summary_result.payload.get("actions_next_48h", []))
                send_analysis_complete(
                    to_email=creator.email,
                    user_name=creator.full_name or "vous",
                    project_title=project.title,
                    project_id=str(project.id),
                    risk_count=risk_count,
                    action_count=action_count,
                )
        except Exception as email_exc:
            import logging
            logging.getLogger(__name__).warning("Email notification failed: %s", email_exc)

        # Dispatch webhook analysis.completed via Celery (async, fail-safe)
        try:
            dispatch_webhook_event.delay(
                str(project.org_id),
                "analysis.completed",
                {"project_id": project_id, "title": project.title, "status": "ready"},
            )
        except Exception as wh_exc:
            import logging
            logging.getLogger(__name__).warning("Webhook dispatch trigger failed: %s", wh_exc)

        return {"project_id": project_id, "status": "ready"}

    except Exception as exc:
        db.rollback()
        project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
        if project:
            project.status = "error"
            db.commit()
        # Stocker le message d'erreur dans Redis pour le frontend
        try:
            import redis as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL)
            error_msg = str(exc)[:500] if exc else "Erreur interne"
            r.set(f"project_error:{project_id}", error_msg, ex=86400)
        except Exception:
            pass
        # Guard : ne relancer que si le quota de retries n'est pas épuisé
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        raise exc  # Max retries atteint → Celery marque FAILURE
    finally:
        db.close()


@celery_app.task(name="export_project_pdf", time_limit=300, soft_time_limit=280)
def export_project_pdf(project_id: str) -> str:
    """Génère un PDF d'export et retourne la clé S3."""
    from app.services.exporter import generate_export_pdf
    from app.services.storage import storage_service
    import uuid as uuid_lib

    db = SyncSession()
    try:
        pdf_bytes = generate_export_pdf(db, project_id)
        s3_key = f"exports/{project_id}/{uuid_lib.uuid4()}.pdf"
        storage_service.upload_bytes(s3_key, pdf_bytes, "application/pdf")
        return s3_key
    finally:
        db.close()


@celery_app.task(name="sync_boamp_all_orgs", time_limit=120)
def sync_boamp_all_orgs():
    """Synchronise les AO BOAMP pour toutes les orgs actives."""
    import uuid as uuid_lib
    from app.models.ao_alert import AoWatchConfig
    from app.services.boamp_watcher import sync_watch_results

    db = SyncSession()
    try:
        # Récupérer toutes les orgs ayant une config veille active
        configs = (
            db.query(AoWatchConfig)
            .filter(AoWatchConfig.is_active.is_(True))
            .all()
        )

        total_new = 0
        for config in configs:
            try:
                new_count = sync_watch_results(db, config.org_id)
                total_new += new_count
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "BOAMP sync échec org=%s : %s", config.org_id, exc
                )

        return {"orgs_synced": len(configs), "new_results": total_new}
    finally:
        db.close()


@celery_app.task(name="send_daily_deadline_reminders", time_limit=120)
def send_daily_deadline_reminders():
    """Envoie des rappels email pour toutes les deadlines dans les 7 prochains jours.

    Tâche Celery beat — exécutée chaque jour à 8h Europe/Paris.
    Pour chaque ProjectDeadline dont deadline_date est entre maintenant et +7 jours,
    envoie un email send_deadline_reminder() aux users de l'org du projet.
    """
    import uuid as uuid_lib
    from datetime import datetime, timezone, timedelta
    from app.models.project import AoProject
    from app.models.user import User
    from app.services.email import send_deadline_reminder

    # Import lazy du modèle ProjectDeadline
    try:
        from app.models.deadline import ProjectDeadline
    except ImportError:
        from app.models.ao_alert import ProjectDeadline  # fallback selon l'organisation du projet

    db = SyncSession()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=7)

    try:
        # Toutes les deadlines à venir dans les 7 jours
        deadlines = (
            db.query(ProjectDeadline)
            .filter(
                ProjectDeadline.deadline_date >= now,
                ProjectDeadline.deadline_date <= cutoff,
            )
            .all()
        )

        sent_count = 0
        for deadline in deadlines:
            try:
                project = db.query(AoProject).filter_by(id=deadline.project_id).first()
                if not project:
                    continue

                # Récupérer tous les users actifs de l'org du projet
                users = db.query(User).filter_by(org_id=project.org_id).all()

                days_remaining = max(0, (deadline.deadline_date - now).days)
                # Affiner : utiliser le calcul en heures pour être précis
                delta_seconds = (deadline.deadline_date - now).total_seconds()
                days_remaining = max(1, int(delta_seconds // 86400) + (1 if delta_seconds % 86400 > 0 else 0))

                for user in users:
                    try:
                        send_deadline_reminder(
                            user_email=user.email,
                            user_name=user.full_name or user.email,
                            project_title=project.title,
                            deadline_description=deadline.label if hasattr(deadline, "label") else deadline.description,
                            days_remaining=days_remaining,
                            project_id=str(project.id),
                            frontend_url=settings.FRONTEND_URL,
                        )
                        sent_count += 1
                    except Exception as user_exc:
                        import logging
                        logging.getLogger(__name__).warning(
                            "Deadline reminder failed user=%s: %s", user.id, user_exc
                        )
            except Exception as deadline_exc:
                import logging
                logging.getLogger(__name__).warning(
                    "Deadline reminder failed deadline=%s: %s", deadline.id, deadline_exc
                )

        return {"deadlines_checked": len(deadlines), "emails_sent": sent_count}
    finally:
        db.close()


@celery_app.task(name="export_project_pack", time_limit=600, soft_time_limit=570)
def export_project_pack(project_id: str) -> str:
    """Génère un ZIP complet (PDF + Word + DPGF Excel + Mémoire technique) et retourne la clé S3."""
    import zipfile
    import uuid as uuid_lib
    from app.services.exporter import generate_export_pdf
    from app.services.docx_exporter import generate_export_docx
    from app.services.memo_exporter import generate_memo_technique
    from app.services.storage import storage_service
    from app.models.document import AoDocument
    from app.services.dpgf_extractor import extract_tables_from_pdf, generate_excel
    from app.models.project import AoProject
    import re
    import logging

    _log = logging.getLogger(__name__)
    db = SyncSession()
    try:
        project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
        safe_title = re.sub(r"[^\w\-]", "_", project.title if project else "export")[:50]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. PDF rapport
            try:
                pdf_bytes = generate_export_pdf(db, project_id)
                zf.writestr(f"rapport_{safe_title}.pdf", pdf_bytes)
            except Exception as e:
                _log.warning(f"[{project_id}] Pack: PDF failed: {e}")

            # 2. Word rapport
            try:
                docx_bytes = generate_export_docx(db, project_id)
                zf.writestr(f"rapport_{safe_title}.docx", docx_bytes)
            except Exception as e:
                _log.warning(f"[{project_id}] Pack: DOCX failed: {e}")

            # 3. Mémoire technique
            try:
                memo_bytes = generate_memo_technique(db, project_id)
                zf.writestr(f"memo_technique_{safe_title}.docx", memo_bytes)
            except Exception as e:
                _log.warning(f"[{project_id}] Pack: Memo failed: {e}")

            # 4. DPGF Excel
            try:
                dpgf_docs = (
                    db.query(AoDocument)
                    .filter(
                        AoDocument.project_id == uuid.UUID(project_id),
                        AoDocument.doc_type.in_(["DPGF", "BPU"]),
                        AoDocument.status == "done",
                    )
                    .all()
                )
                if dpgf_docs:
                    all_tables = []
                    for doc in dpgf_docs:
                        try:
                            pdf_b = storage_service.download_bytes(doc.s3_key)
                            tables = extract_tables_from_pdf(pdf_b, filename=doc.original_name)
                            all_tables.extend(tables)
                        except Exception:
                            pass
                    if all_tables:
                        excel_bytes = generate_excel(all_tables, project_title=project.title if project else "")
                        zf.writestr(f"DPGF_{safe_title}.xlsx", excel_bytes)
            except Exception as e:
                _log.warning(f"[{project_id}] Pack: DPGF failed: {e}")

        zip_buffer.seek(0)
        s3_key = f"exports/{project_id}/{uuid_lib.uuid4()}.zip"
        storage_service.upload_bytes(s3_key, zip_buffer.read(), "application/zip")
        return s3_key
    finally:
        db.close()


@celery_app.task(name="export_project_docx", time_limit=300, soft_time_limit=280)
def export_project_docx(project_id: str) -> str:
    """Génère un rapport Word (.docx) et retourne la clé S3. Plan Pro requis (vérifié en route)."""
    from app.services.docx_exporter import generate_export_docx
    from app.services.storage import storage_service
    import uuid as uuid_lib

    db = SyncSession()
    try:
        docx_bytes = generate_export_docx(db, project_id)
        s3_key = f"exports/{project_id}/{uuid_lib.uuid4()}.docx"
        storage_service.upload_bytes(
            s3_key,
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return s3_key
    finally:
        db.close()


@celery_app.task(name="purge_expired_data", time_limit=300, soft_time_limit=280)
def purge_expired_data():
    """Purge les données expirées selon la rétention du plan de chaque organisation.

    Tâche Celery beat — exécutée chaque nuit à 3h Europe/Paris.
    Pour chaque organisation, supprime :
    - Les projets (et leurs documents/analyses) dépassant la durée de rétention
    - Les exports S3 correspondants

    Rétentions par plan :
    - free/trial : 7-14 jours
    - starter : 30 jours
    - pro : 90 jours
    - europe : 180 jours
    - business : 365 jours
    """
    import logging
    from datetime import datetime, timezone, timedelta
    from app.models.organization import Organization
    from app.models.project import AoProject
    from app.models.document import AoDocument
    from app.services.billing import PLANS

    _log = logging.getLogger(__name__)
    db = SyncSession()

    try:
        now = datetime.now(timezone.utc)
        orgs = db.query(Organization).filter(Organization.deleted_at.is_(None)).all()

        total_purged = 0

        for org in orgs:
            plan_config = PLANS.get(org.plan, PLANS.get("free"))
            if not plan_config:
                continue

            retention_days = plan_config.retention_days
            cutoff_date = now - timedelta(days=retention_days)

            # Trouver les projets expirés
            expired_projects = (
                db.query(AoProject)
                .filter(
                    AoProject.org_id == org.id,
                    AoProject.created_at < cutoff_date,
                )
                .all()
            )

            if not expired_projects:
                continue

            for project in expired_projects:
                try:
                    docs = db.query(AoDocument).filter_by(project_id=project.id).all()
                    for doc in docs:
                        if doc.s3_key:
                            try:
                                from app.services.storage import storage_service
                                storage_service.delete_object(doc.s3_key)
                            except Exception:
                                pass  # S3 cleanup best-effort
                    db.delete(project)
                    total_purged += 1
                except Exception as exc:
                    _log.warning("purge_project_failed project=%s: %s", project.id, exc)

            db.commit()
            if expired_projects:
                _log.info(
                    "purge_completed org=%s plan=%s retention=%dd purged=%d",
                    org.id, org.plan, retention_days, len(expired_projects),
                )

        return {"organizations_checked": len(orgs), "projects_purged": total_purged}

    except Exception as exc:
        _log.error("purge_expired_data_failed: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="dispatch_webhook_event", time_limit=30, soft_time_limit=25)
def dispatch_webhook_event(org_id: str, event_type: str, data: dict):
    """Fan-out : récupère les endpoints abonnés et lance une task deliver_webhook par endpoint.

    Architecture fan-out :
    1. Ce task récupère la liste des endpoints éligibles (DB query sync)
    2. Construit le payload JSON signé
    3. Lance N tasks deliver_webhook en parallèle (une par endpoint)

    Chaque deliver_webhook a son propre retry backoff — un endpoint lent
    ne bloque plus les autres.
    """
    import asyncio
    import json
    import logging as _logging
    from datetime import datetime, timezone
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as _AsyncSession
    from sqlalchemy.orm import sessionmaker as _sessionmaker
    from app.services.webhook_dispatch import get_subscribed_endpoints

    _log = _logging.getLogger(__name__)

    async def _get_endpoints():
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        async_session = _sessionmaker(engine, class_=_AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            endpoints = await get_subscribed_endpoints(session, org_id, event_type)
        await engine.dispose()
        return endpoints

    try:
        loop = asyncio.new_event_loop()
        endpoints = loop.run_until_complete(_get_endpoints())
        loop.close()
    except Exception as exc:
        _log.error("webhook_fanout_failed event=%s org=%s: %s", event_type, org_id, exc)
        raise

    if not endpoints:
        _log.info("webhook_no_endpoints event=%s org=%s", event_type, org_id)
        return {"event": event_type, "org_id": org_id, "dispatched": 0}

    # Construire le payload une seule fois
    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)

    # Fan-out : une task par endpoint
    for ep in endpoints:
        deliver_webhook.delay(
            endpoint_id=ep["endpoint_id"],
            url=ep["url"],
            secret=ep["secret"],
            event_type=event_type,
            payload_json=payload_json,
        )

    _log.info(
        "webhook_fanout_complete event=%s org=%s dispatched=%d",
        event_type, org_id, len(endpoints),
    )
    return {"event": event_type, "org_id": org_id, "dispatched": len(endpoints)}


@celery_app.task(
    name="deliver_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=10,  # 10s, 20s, 40s (backoff exponentiel)
    time_limit=30,
    soft_time_limit=20,
    acks_late=True,
)
def deliver_webhook(
    self,
    endpoint_id: str,
    url: str,
    secret: str,
    event_type: str,
    payload_json: str,
):
    """Livre un webhook à un endpoint unique avec retry backoff exponentiel.

    Retry policy :
    - Max 3 retries (4 tentatives au total)
    - Backoff : 10s → 20s → 40s
    - Après 3 échecs, le webhook est loggé en dead letter (pas de perte silencieuse)
    """
    import logging as _logging
    from app.services.webhook_dispatch import deliver_single_webhook_sync

    _log = _logging.getLogger(__name__)
    attempt = self.request.retries + 1

    result = deliver_single_webhook_sync(
        endpoint_id=endpoint_id,
        url=url,
        secret=secret,
        event_type=event_type,
        payload_json=payload_json,
        attempt_number=attempt,
    )

    if result["success"]:
        return result

    # Échec — retry avec backoff exponentiel
    if self.request.retries < self.max_retries:
        backoff = 10 * (2 ** self.request.retries)  # 10, 20, 40 secondes
        _log.warning(
            "webhook_retry attempt=%d/%d backoff=%ds endpoint=%s event=%s error=%s",
            attempt, self.max_retries + 1, backoff, url, event_type, result["error"],
        )
        raise self.retry(countdown=backoff)

    # Tous les retries épuisés — dead letter log
    _log.error(
        "webhook_dead_letter endpoint=%s event=%s attempts=%d last_error=%s",
        url, event_type, attempt, result["error"],
    )
    return {**result, "dead_letter": True, "total_attempts": attempt}
