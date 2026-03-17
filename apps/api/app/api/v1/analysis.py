import uuid
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis as redis_lib

from sqlalchemy import func as sa_func

from app.database import get_db
from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem
from app.models.deadline import ProjectDeadline
from app.models.user import User
from app.models.organization import Organization
from app.services.billing import billing_service
from app.schemas.analysis import (
    SummaryOut, ChecklistOut, ChecklistItemOut, ChecklistItemUpdate,
    CriteriaOut, AnalysisStatusOut
)
from app.api.v1.deps import get_current_user, get_current_org
from app.config import settings
from app.core.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Lazy Redis init — pas de connexion bloquante au démarrage ──────────────
_redis_client: redis_lib.Redis | None = None


def get_redis() -> redis_lib.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def _get_project_or_404(project_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> AoProject:
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return p


@router.post("/{project_id}/analyze", status_code=202)
@limiter.limit("5/minute")
async def trigger_analysis(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    project = await _get_project_or_404(project_id, org.id, db)

    if project.status == "analyzing":
        return {"message": "Analyse déjà en cours", "project_id": str(project_id)}

    # Quota check — empêche le Denial-of-Wallet
    await billing_service.enforce_quota(org, db)

    # Pré-validation : au moins 1 document traité
    doc_count_result = await db.execute(
        select(sa_func.count(AoDocument.id)).where(
            AoDocument.project_id == project_id,
            AoDocument.status == "done",
        )
    )
    if (doc_count_result.scalar_one() or 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="Aucun document traité dans ce projet. Uploadez au moins un document avant de lancer l'analyse.",
        )

    # OCR quality gating — avertir si qualité moyenne < 40%
    ocr_warning = None
    ocr_avg_result = await db.execute(
        select(sa_func.avg(AoDocument.ocr_quality_score)).where(
            AoDocument.project_id == project_id,
            AoDocument.status == "done",
            AoDocument.ocr_quality_score.isnot(None),
        )
    )
    ocr_avg = ocr_avg_result.scalar_one()
    if ocr_avg is not None and ocr_avg < 40:
        ocr_warning = (
            f"Qualité OCR moyenne faible ({ocr_avg:.0f}%). "
            "Les résultats d'analyse peuvent être imprécis. "
            "Privilégiez des PDFs textuels ou des scans de meilleure qualité."
        )

    from app.worker.tasks import analyze_project
    task = analyze_project.delay(str(project_id))

    # Stocker le task_id dans Redis pour suivi de progression (24h TTL)
    try:
        get_redis().set(f"project_task:{project_id}", task.id, ex=86400)
    except Exception as e:
        logger.warning(f"Impossible de stocker task_id dans Redis: {e}")

    project.status = "analyzing"
    await db.flush()

    response = {"message": "Analyse lancée", "project_id": str(project_id), "task_id": task.id}
    if ocr_warning:
        response["ocr_warning"] = ocr_warning
    return response


@router.get("/{project_id}/analyze/status", response_model=AnalysisStatusOut)
async def get_analysis_status(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    project = await _get_project_or_404(project_id, org.id, db)

    progress_pct = 0
    current_step = "En attente"

    if project.status == "ready":
        progress_pct = 100
        current_step = "Analyse terminée"

    elif project.status == "analyzing":
        # Lire la vraie progression depuis Redis (stockée par _set_progress dans tasks.py)
        try:
            redis = get_redis()
            task_id = redis.get(f"project_task:{project_id}")
            if task_id:
                progress_data = redis.get(f"progress:{task_id}")
                if progress_data:
                    prog = json.loads(progress_data)
                    progress_pct = prog.get("pct", 50)
                    current_step = prog.get("step", "Analyse en cours...")
                else:
                    progress_pct = 50
                    current_step = "Analyse en cours..."
            else:
                progress_pct = 50
                current_step = "Analyse en cours..."
        except Exception as e:
            logger.warning(f"Lecture progression Redis échouée: {e}")
            progress_pct = 50
            current_step = "Analyse en cours..."

    elif project.status == "error":
        progress_pct = 0
        try:
            error_msg = get_redis().get(f"project_error:{project_id}")
        except Exception:
            error_msg = None
        current_step = error_msg or "L'analyse a échoué. Veuillez réessayer."

    elif project.status == "draft":
        progress_pct = 0
        current_step = "En attente de lancement"

    return AnalysisStatusOut(
        project_id=project_id,
        status=project.status,
        progress_pct=progress_pct,
        current_step=current_step,
    )


@router.get("/{project_id}/summary")
async def get_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "summary",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    er = result.scalars().first()
    if not er:
        raise HTTPException(status_code=404, detail="Résumé non disponible — lancez l'analyse d'abord")
    return er.payload


@router.get("/{project_id}/checklist", response_model=ChecklistOut)
async def get_checklist(
    project_id: uuid.UUID,
    criticality: str | None = None,
    status_filter: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)

    q = select(ChecklistItem).where(ChecklistItem.project_id == project_id)
    if criticality:
        q = q.where(ChecklistItem.criticality == criticality)
    if status_filter:
        q = q.where(ChecklistItem.status == status_filter)
    if category:
        q = q.where(ChecklistItem.category == category)

    q = q.order_by(ChecklistItem.criticality, ChecklistItem.category)
    result = await db.execute(q)
    items = list(result.scalars().all())

    # Stats sur tous les items (sans filtre)
    all_result = await db.execute(select(ChecklistItem).where(ChecklistItem.project_id == project_id))
    all_items = list(all_result.scalars().all())

    by_status = {"OK": 0, "MANQUANT": 0, "À CLARIFIER": 0}
    by_crit = {"Éliminatoire": 0, "Important": 0, "Info": 0}
    for i in all_items:
        if i.status in by_status:
            by_status[i.status] += 1
        if i.criticality in by_crit:
            by_crit[i.criticality] += 1

    return ChecklistOut(
        total=len(all_items),
        by_status=by_status,
        by_criticality=by_crit,
        checklist=[ChecklistItemOut.model_validate(i) for i in items],
    )


@router.patch("/{project_id}/checklist/{item_id}", response_model=ChecklistItemOut)
async def update_checklist_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ChecklistItem).where(ChecklistItem.id == item_id, ChecklistItem.project_id == project_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item introuvable")

    # Seuls les champs définis dans le schema sont mis à jour (injection impossible)
    update_data = data.model_dump(exclude_none=True)
    for k, v in update_data.items():
        setattr(item, k, v)
    await db.flush()
    await db.refresh(item)
    return ChecklistItemOut.model_validate(item)


# ── Go/No-Go ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/gonogo")
async def get_gonogo(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne le score Go/No-Go calculé lors de l'analyse."""
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "gonogo",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    er = result.scalars().first()
    if not er:
        raise HTTPException(status_code=404, detail="Score Go/No-Go non disponible — lancez l'analyse d'abord")
    return er.payload


# ── Chat DCE ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str


@router.post("/{project_id}/chat")
@limiter.limit("20/hour")
async def chat_with_dce(
    request: Request,
    project_id: uuid.UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Chat RAG : pose une question sur le DCE et obtiens une réponse sourcée."""
    project = await _get_project_or_404(project_id, org.id, db)
    if project.status not in ("ready", "analyzing"):
        raise HTTPException(status_code=400, detail="L'analyse doit être terminée pour utiliser le chat")

    from app.services.retriever import retrieve_relevant_chunks, format_context
    from app.services.llm import llm_service
    from app.services.prompts import build_chat_prompt
    import asyncio

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question trop longue (max 500 caractères)")

    # RAG : récupérer les chunks pertinents (sync dans thread)
    from app.worker.tasks import SyncSession
    loop = asyncio.get_running_loop()
    def _retrieve():
        sync_db = SyncSession()
        try:
            return retrieve_relevant_chunks(sync_db, str(project_id), question, top_k=6)
        finally:
            sync_db.close()
    chunks = await loop.run_in_executor(None, _retrieve)
    context = format_context(chunks)

    sys_p, usr_p = build_chat_prompt(question, context)

    # Appel LLM Claude (sync dans thread)
    try:
        raw_answer = await loop.run_in_executor(
            None,
            lambda: llm_service._anthropic_json(sys_p, usr_p)
        )
        if isinstance(raw_answer, dict):
            answer = raw_answer.get("answer", str(raw_answer))
        else:
            answer = str(raw_answer)
    except Exception:
        # Fallback : réponse texte libre
        try:
            answer = await loop.run_in_executor(
                None,
                lambda: llm_service.chat_text(sys_p, usr_p)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur LLM: {str(e)}")

    citations = [
        {
            "doc_name": c["doc_name"],
            "page_start": c["page_start"],
            "page_end": c["page_end"],
            "doc_type": c["doc_type"],
            "snippet": c["content"][:150] + "…" if len(c["content"]) > 150 else c["content"],
        }
        for c in chunks[:3]
    ]

    return {"answer": answer, "citations": citations, "chunks_used": len(chunks)}


@router.post("/{project_id}/chat/stream")
@limiter.limit("20/hour")
async def chat_with_dce_stream(
    request: Request,
    project_id: uuid.UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Chat RAG en streaming SSE — affichage progressif token par token."""
    project = await _get_project_or_404(project_id, org.id, db)
    if project.status not in ("ready", "analyzing"):
        raise HTTPException(status_code=400, detail="L'analyse doit être terminée pour utiliser le chat")

    from app.services.retriever import retrieve_relevant_chunks, format_context
    from app.services.llm import llm_service
    from app.services.prompts import build_chat_prompt
    import asyncio

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question trop longue (max 500 caractères)")

    # RAG : récupérer les chunks pertinents (sync dans thread)
    from app.worker.tasks import SyncSession
    loop = asyncio.get_running_loop()

    def _retrieve():
        sync_db = SyncSession()
        try:
            return retrieve_relevant_chunks(sync_db, str(project_id), question, top_k=6)
        finally:
            sync_db.close()

    chunks = await loop.run_in_executor(None, _retrieve)
    context = format_context(chunks)
    sys_p, usr_p = build_chat_prompt(question, context)

    citations = [
        {
            "doc_name": c.get("doc_name", ""),
            "page_start": c.get("page_start", 1),
            "page_end": c.get("page_end", 1),
            "doc_type": c.get("doc_type", ""),
        }
        for c in chunks[:4]
    ]

    async def event_generator():
        import json as _json
        # Envoyer les citations d'abord
        yield f"data: {_json.dumps({'type': 'citations', 'citations': citations})}\n\n"
        # Streamer les tokens via run_in_executor (stream_chat_text est synchrone)
        try:
            tokens = await loop.run_in_executor(
                None,
                lambda: list(llm_service.stream_chat_text(sys_p, usr_p))
            )
            for token in tokens:
                yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"
        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Writing assistant ────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    pass  # Pas de body requis, tout vient de l'item


@router.post("/{project_id}/checklist/{item_id}/generate")
@limiter.limit("30/hour")
async def generate_checklist_response(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Génère un texte de réponse pour un item de checklist (assistant rédaction)."""
    await _get_project_or_404(project_id, org.id, db)

    # Vérifier le plan (Pro+ uniquement)
    if org.plan not in ("pro", "europe", "business"):
        raise HTTPException(
            status_code=403,
            detail="L'assistant rédaction est disponible à partir du plan Pro"
        )

    item_result = await db.execute(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id,
            ChecklistItem.project_id == project_id,
        )
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist introuvable")

    from app.services.retriever import retrieve_relevant_chunks, format_context
    from app.services.llm import llm_service
    from app.services.prompts import build_writing_prompt
    import asyncio

    from app.worker.tasks import SyncSession
    loop = asyncio.get_running_loop()
    query = f"{item.requirement} {item.what_to_provide or ''}"
    def _retrieve_writing():
        sync_db = SyncSession()
        try:
            return retrieve_relevant_chunks(sync_db, str(project_id), query, top_k=5)
        finally:
            sync_db.close()
    chunks = await loop.run_in_executor(None, _retrieve_writing)
    context = format_context(chunks)

    sys_p, usr_p = build_writing_prompt(
        requirement=item.requirement or "",
        what_to_provide=item.what_to_provide or "",
        context=context,
    )

    try:
        result = await loop.run_in_executor(
            None,
            lambda: llm_service.complete_json(sys_p, usr_p, required_keys=["generated_text"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération: {str(e)}")

    return {
        "generated_text": result.get("generated_text", ""),
        "key_points_addressed": result.get("key_points_addressed", []),
        "word_count": result.get("word_count", 0),
        "item_requirement": item.requirement,
        "item_id": str(item_id),
    }


# ── Timeline / Échéances ─────────────────────────────────────────────────────

@router.get("/{project_id}/timeline")
async def get_timeline(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne la timeline extraite du DCE avec les tâches suggérées."""
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "timeline",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    er = result.scalars().first()
    if not er:
        raise HTTPException(status_code=404, detail="Timeline non disponible — lancez l'analyse d'abord")
    return er.payload


@router.patch("/{project_id}/timeline/tasks/{task_index}")
async def update_timeline_task(
    project_id: uuid.UUID,
    task_index: int,
    done: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Marque une tâche de la timeline comme faite ou non."""
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "timeline",
        ).order_by(ExtractionResult.version.desc())
    )
    er = result.scalar_one_or_none()
    if not er:
        raise HTTPException(status_code=404, detail="Timeline introuvable")

    payload = dict(er.payload)
    tasks = payload.get("suggested_tasks", [])
    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(status_code=400, detail="Index de tâche invalide")

    tasks[task_index]["done"] = done
    payload["suggested_tasks"] = tasks
    er.payload = payload
    await db.flush()
    return payload


@router.get("/{project_id}/criteria")
async def get_criteria(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "criteria",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    er = result.scalars().first()
    if not er:
        raise HTTPException(status_code=404, detail="Critères non disponibles — lancez l'analyse d'abord")
    return er.payload


# ── Deadlines / Alertes dates clés ──────────────────────────────────────────

@router.get("/{project_id}/deadlines")
async def get_deadlines(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne la liste des dates clés structurées du projet, triées par date croissante."""
    await _get_project_or_404(project_id, org.id, db)

    result = await db.execute(
        select(ProjectDeadline)
        .where(ProjectDeadline.project_id == project_id)
        .order_by(ProjectDeadline.deadline_date.asc())
    )
    deadlines = list(result.scalars().all())

    return [
        {
            "id": str(d.id),
            "project_id": str(d.project_id),
            "deadline_type": d.deadline_type,
            "label": d.label,
            "deadline_date": d.deadline_date.isoformat(),
            "is_critical": d.is_critical,
            "citation": d.citation,
            "created_at": d.created_at.isoformat(),
        }
        for d in deadlines
    ]


# ── Analyse des risques CCAP ─────────────────────────────────────────────────

@router.get("/{project_id}/ccap-risks")
@limiter.limit("10/hour")
async def get_ccap_risks(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Analyse les clauses risquées du CCAP et retourne un rapport structuré.

    Tente de récupérer le résultat mis en cache (result_type='ccap_risks').
    Si absent, agrège le texte des documents CCAP du projet et lance l'analyse LLM.
    Le résultat est ensuite mis en cache dans ExtractionResult pour éviter les re-analyses.
    """
    from app.models.document import AoDocument, DocumentPage
    from app.services.ccap_analyzer import analyze_ccap_risks
    import asyncio

    await _get_project_or_404(project_id, org.id, db)

    # ── 1. Vérifier le cache ────────────────────────────────────────────────
    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "ccap_risks",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cached_result = cached.scalars().first()
    if cached_result:
        logger.info(f"[{project_id}] CCAP risks — retour depuis cache (v{cached_result.version})")
        return cached_result.payload

    # ── 2. Récupérer les documents CCAP ────────────────────────────────────
    docs_result = await db.execute(
        select(AoDocument).where(
            AoDocument.project_id == project_id,
            AoDocument.doc_type == "CCAP",
            AoDocument.status == "done",
        )
    )
    ccap_docs = list(docs_result.scalars().all())

    if not ccap_docs:
        return {
            "clauses_risquees": [],
            "score_risque_global": 0,
            "nb_clauses_critiques": 0,
            "resume_risques": "",
            "no_ccap_document": True,
            "message": "Aucun document CCAP trouvé pour ce projet. Uploadez un CCAP pour activer l'analyse des risques.",
        }

    # ── 3. Agréger le texte des pages CCAP ─────────────────────────────────
    all_text_parts: list[str] = []
    for doc in ccap_docs:
        pages_result = await db.execute(
            select(DocumentPage).where(
                DocumentPage.document_id == doc.id
            ).order_by(DocumentPage.page_num)
        )
        pages = list(pages_result.scalars().all())
        doc_text = "\n".join(p.raw_text for p in pages if p.raw_text)
        if doc_text.strip():
            all_text_parts.append(f"=== Document : {doc.original_name} ===\n{doc_text}")

    full_text = "\n\n".join(all_text_parts)

    if not full_text.strip():
        return {
            "clauses_risquees": [],
            "score_risque_global": 0,
            "nb_clauses_critiques": 0,
            "resume_risques": "",
            "no_ccap_text": True,
            "message": "Le document CCAP n'a pas de texte extrait. Vérifiez que l'extraction OCR a été effectuée.",
        }

    # ── 4. Lancer l'analyse LLM (dans un thread — appel synchrone) ─────────
    loop = asyncio.get_running_loop()
    try:
        analysis = await loop.run_in_executor(
            None,
            lambda: analyze_ccap_risks(full_text, project_id=str(project_id)),
        )
    except Exception as exc:
        logger.error(f"[{project_id}] Erreur analyse CCAP: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse des risques CCAP : {str(exc)}",
        )

    # ── 5. Mettre en cache le résultat ─────────────────────────────────────
    payload = {
        "clauses_risquees": analysis["clauses_risquees"],
        "score_risque_global": analysis["score_risque_global"],
        "nb_clauses_critiques": analysis["nb_clauses_critiques"],
        "resume_risques": analysis.get("resume_risques", ""),
        "ccap_docs_analyzed": [doc.original_name for doc in ccap_docs],
        "model_used": analysis.get("model_used", ""),
    }

    new_result = ExtractionResult(
        project_id=project_id,
        result_type="ccap_risks",
        payload=payload,
        model_used=analysis.get("model_used"),
    )
    db.add(new_result)
    await db.flush()

    logger.info(
        f"[{project_id}] CCAP risks — analyse terminée et mise en cache "
        f"(score={analysis['score_risque_global']}, "
        f"clauses={len(analysis['clauses_risquees'])})"
    )

    return payload


# ═══════════════════════════════════════════════════════════════════════════════
# NOUVELLES ANALYSES — Sprint V + W
# ═══════════════════════════════════════════════════════════════════════════════


async def _get_doc_text_by_type(
    db: AsyncSession, project_id: uuid.UUID, doc_type: str,
) -> tuple[str, list[str]]:
    """Récupère le texte agrégé des documents d'un type donné."""
    from app.models.document import AoDocument, DocumentPage

    docs_result = await db.execute(
        select(AoDocument).where(
            AoDocument.project_id == project_id,
            AoDocument.doc_type == doc_type,
            AoDocument.status == "done",
        )
    )
    docs = list(docs_result.scalars().all())
    if not docs:
        return "", []

    all_text_parts: list[str] = []
    doc_names: list[str] = []
    for doc in docs:
        pages_result = await db.execute(
            select(DocumentPage).where(
                DocumentPage.document_id == doc.id
            ).order_by(DocumentPage.page_num)
        )
        pages = list(pages_result.scalars().all())
        doc_text = "\n".join(p.raw_text for p in pages if p.raw_text)
        if doc_text.strip():
            all_text_parts.append(f"=== Document : {doc.original_name} ===\n{doc_text}")
            doc_names.append(doc.original_name)

    return "\n\n".join(all_text_parts), doc_names


# ── V1 : Analyse RC (Règlement de Consultation) ─────────────────────────────

@router.get("/{project_id}/rc-analysis")
@limiter.limit("10/hour")
async def get_rc_analysis(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Analyse le Règlement de Consultation : qui peut candidater, groupement, sous-traitance."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.rc_analyzer import analyze_rc

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "rc_analysis",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    full_text, doc_names = await _get_doc_text_by_type(db, project_id, "RC")
    if not full_text.strip():
        return {"message": "Aucun document RC trouvé. Uploadez un Règlement de Consultation.", "no_rc_document": True}

    import asyncio
    analysis = await asyncio.get_running_loop().run_in_executor(
        None, lambda: analyze_rc(full_text, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="rc_analysis",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── V2 : Analyse AE (Acte d'Engagement) ─────────────────────────────────────

@router.get("/{project_id}/ae-analysis")
@limiter.limit("10/hour")
async def get_ae_analysis(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Analyse l'Acte d'Engagement : prix, durée, pénalités, garanties, clauses risquées."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.ae_analyzer import analyze_ae

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "ae_analysis",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    full_text, doc_names = await _get_doc_text_by_type(db, project_id, "AE")
    if not full_text.strip():
        return {"message": "Aucun document AE trouvé. Uploadez un Acte d'Engagement.", "no_ae_document": True}

    import asyncio
    analysis = await asyncio.get_running_loop().run_in_executor(
        None, lambda: analyze_ae(full_text, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="ae_analysis",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── V2b : Analyse CCTP (Cahier des Clauses Techniques Particulières) ─────────

@router.get("/{project_id}/cctp-analysis")
@limiter.limit("10/hour")
async def get_cctp_analysis(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Analyse le CCTP : exigences techniques, normes DTU, matériaux, essais, risques."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.cctp_analyzer import analyze_cctp

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "cctp_analysis",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    full_text, doc_names = await _get_doc_text_by_type(db, project_id, "CCTP")
    if not full_text.strip():
        return {"message": "Aucun document CCTP trouvé. Uploadez un Cahier des Clauses Techniques.", "no_cctp_document": True}

    import asyncio
    analysis = await asyncio.get_running_loop().run_in_executor(
        None, lambda: analyze_cctp(full_text, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="cctp_analysis",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── V2c : Simulation trésorerie / Cash-flow ────────────────────────────────

@router.get("/{project_id}/cashflow-simulation")
async def get_cashflow_simulation(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Simule la trésorerie du marché à partir des données AE (avance, retenue, délai paiement)."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.cashflow_simulator import simulate_cashflow
    import asyncio

    # Vérifier le cache
    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "cashflow_simulation",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    # Récupérer les données AE pour alimenter le simulateur
    ae_result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "ae_analysis",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    ae = ae_result.scalars().first()

    # Valeurs par défaut si pas d'AE analysé
    montant_total_ht = 500_000.0
    duree_mois = 12
    avance_pct = 5.0
    retenue_pct = 5.0
    delai_paiement_jours = 30
    marge_brute_pct = 15.0

    if ae and ae.payload:
        p = ae.payload
        # Extraire le montant total HT
        montant = p.get("montant_total_ht") or p.get("montant_marche_ht")
        if montant and isinstance(montant, (int, float)) and montant > 0:
            montant_total_ht = float(montant)

        # Extraire la durée en mois
        duree = p.get("duree_mois") or p.get("duree_marche_mois")
        if duree and isinstance(duree, (int, float)) and duree > 0:
            duree_mois = int(duree)

        # Extraire le pourcentage d'avance
        avance = p.get("avance_pct") or p.get("avance_forfaitaire_pct")
        if avance is not None and isinstance(avance, (int, float)):
            avance_pct = float(avance)

        # Extraire le pourcentage de retenue de garantie
        retenue = p.get("retenue_garantie_pct")
        if retenue is not None and isinstance(retenue, (int, float)):
            retenue_pct = float(retenue)

        # Extraire le délai de paiement
        delai = p.get("delai_paiement_jours")
        if delai and isinstance(delai, (int, float)) and delai > 0:
            delai_paiement_jours = int(delai)

    simulation = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: simulate_cashflow(
            montant_total_ht=montant_total_ht,
            duree_mois=duree_mois,
            avance_pct=avance_pct,
            retenue_pct=retenue_pct,
            delai_paiement_jours=delai_paiement_jours,
            marge_brute_pct=marge_brute_pct,
        ),
    )

    # Ajouter la source des données
    simulation["source_ae"] = ae is not None
    simulation["message"] = (
        "Simulation basée sur les données de l'Acte d'Engagement."
        if ae else
        "Simulation avec valeurs par défaut — uploadez un Acte d'Engagement pour des données réelles."
    )

    # Cache le résultat
    new_er = ExtractionResult(
        project_id=project_id, result_type="cashflow_simulation",
        payload=simulation, model_used="deterministic",
    )
    db.add(new_er)
    await db.flush()
    return simulation


# ── V3 : Vérificateur DC1/DC2 + attestations ────────────────────────────────

@router.get("/{project_id}/dc-check")
@limiter.limit("10/hour")
async def get_dc_check(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Vérifie les documents administratifs requis (DC1, DC2, attestations, certifications)."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.dc_checker import analyze_dc_requirements
    from app.services.retriever import retrieve_relevant_chunks, format_context
    import asyncio

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "dc_check",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    from app.worker.tasks import SyncSession
    loop = asyncio.get_running_loop()
    dc_query = "DC1 DC2 Kbis attestation URSSAF fiscale assurance certification Qualibat pièces administratives candidature"
    def _retrieve():
        sync_db = SyncSession()
        try:
            return retrieve_relevant_chunks(sync_db, str(project_id), dc_query, top_k=20)
        finally:
            sync_db.close()
    chunks = await loop.run_in_executor(None, _retrieve)

    if not chunks:
        return {"message": "Aucun contexte administratif trouvé dans les documents.", "no_dc_context": True}

    context = format_context(chunks)
    analysis = await loop.run_in_executor(
        None, lambda: analyze_dc_requirements(context, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="dc_check",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── V4 : Détecteur de conflits intra-DCE ─────────────────────────────────────

@router.get("/{project_id}/conflicts")
@limiter.limit("10/hour")
async def get_conflicts(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Détecte les conflits et contradictions entre les pièces du DCE."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.conflict_detector import detect_conflicts
    import asyncio

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "conflicts",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    texts: dict[str, str] = {}
    for doc_type in ("RC", "CCTP", "CCAP", "AE"):
        text, _ = await _get_doc_text_by_type(db, project_id, doc_type)
        if text.strip():
            texts[doc_type] = text

    if len(texts) < 2:
        return {
            "message": "Au moins 2 types de documents différents sont nécessaires pour détecter les conflits.",
            "no_conflicts_possible": True,
            "docs_found": list(texts.keys()),
        }

    analysis = await asyncio.get_running_loop().run_in_executor(
        None, lambda: detect_conflicts(texts, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="conflicts",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── W2 : Assistant Questions aux Acheteurs ───────────────────────────────────

@router.get("/{project_id}/questions")
@limiter.limit("10/hour")
async def get_questions(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Génère les questions pertinentes à poser à l'acheteur."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.questions_generator import generate_questions
    from app.services.retriever import retrieve_relevant_chunks, format_context
    import asyncio

    cached = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "questions",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    cr = cached.scalars().first()
    if cr:
        return cr.payload

    from app.worker.tasks import SyncSession
    loop = asyncio.get_running_loop()
    def _retrieve():
        sync_db = SyncSession()
        try:
            q = "ambiguïtés incohérences questions éclaircissements précisions manquantes"
            return retrieve_relevant_chunks(sync_db, str(project_id), q, top_k=15)
        finally:
            sync_db.close()
    chunks = await loop.run_in_executor(None, _retrieve)
    context = format_context(chunks)

    summary_er = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "summary",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    summary = summary_er.scalars().first()
    summary_payload = summary.payload if summary else None

    analysis = await loop.run_in_executor(
        None, lambda: generate_questions(context, summary_payload=summary_payload, project_id=str(project_id))
    )

    new_er = ExtractionResult(
        project_id=project_id, result_type="questions",
        payload=analysis, model_used=analysis.get("model_used", ""),
    )
    db.add(new_er)
    await db.flush()
    return analysis


# ── W3 : Simulateur scoring acheteur ─────────────────────────────────────────

@router.get("/{project_id}/scoring-simulation")
async def get_scoring_simulation(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Simule la note que l'acheteur donnerait à l'offre."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.scoring_simulator import simulate_scoring
    import asyncio

    criteria_er = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "criteria",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    criteria = criteria_er.scalars().first()
    if not criteria:
        raise HTTPException(status_code=400, detail="L'analyse des critères doit être effectuée d'abord")

    project_res = await db.execute(select(AoProject).where(AoProject.id == project_id))
    proj = project_res.scalar_one()
    from app.models.company_profile import CompanyProfile
    cp_result = await db.execute(select(CompanyProfile).where(CompanyProfile.org_id == proj.org_id))
    cp = cp_result.scalars().first()
    company_profile = None
    if cp:
        company_profile = {
            "revenue_eur": cp.revenue_eur, "employee_count": cp.employee_count,
            "certifications": cp.certifications or [], "specialties": cp.specialties or [],
            "regions": cp.regions or [],
        }

    analysis = await asyncio.get_running_loop().run_in_executor(
        None, lambda: simulate_scoring(criteria.payload, company_profile=company_profile, project_id=str(project_id))
    )
    return analysis


# ── V5 : DPGF Pricing Intelligence ──────────────────────────────────────────

@router.get("/{project_id}/dpgf-pricing")
async def get_dpgf_pricing(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Compare les prix DPGF aux référentiels BTP (indicatif)."""
    await _get_project_or_404(project_id, org.id, db)
    from app.services.btp_pricing import check_dpgf_pricing
    from app.services.dpgf_extractor import extract_tables_from_pdf
    from app.models.document import AoDocument
    from app.models.company_profile import CompanyProfile
    from app.services.storage import storage_service
    import asyncio

    # Fetch company profile region for geo-adjusted pricing
    cp_result = await db.execute(select(CompanyProfile).where(CompanyProfile.org_id == org.id))
    cp = cp_result.scalars().first()
    region = cp.regions[0] if cp and cp.regions else None

    docs_result = await db.execute(
        select(AoDocument).where(
            AoDocument.project_id == project_id,
            AoDocument.doc_type.in_(["DPGF", "BPU"]),
            AoDocument.status == "done",
        )
    )
    dpgf_docs = list(docs_result.scalars().all())
    if not dpgf_docs:
        return {"message": "Aucun document DPGF/BPU trouvé.", "pricing_analysis": []}

    all_pricing: list[dict] = []
    loop = asyncio.get_running_loop()
    for doc in dpgf_docs[:2]:
        try:
            pdf_bytes = await loop.run_in_executor(None, lambda d=doc: storage_service.download_bytes(d.s3_key))
            tables = await loop.run_in_executor(None, lambda b=pdf_bytes, n=doc.original_name: extract_tables_from_pdf(b, n))
            for table in tables:
                rows_dicts = [
                    {"designation": getattr(r, "designation", ""), "prix_unitaire": getattr(r, "prix_unitaire", "")}
                    for r in table.rows
                ]
                pricing_results = check_dpgf_pricing(rows_dicts, region=region or "france")
                all_pricing.extend(pricing_results)
        except Exception as exc:
            logger.warning(f"[{project_id}] DPGF pricing error for {doc.original_name}: {exc}")

    return {
        "pricing_analysis": all_pricing,
        "total_lines": len(all_pricing),
        "alerts": [p for p in all_pricing if p.get("status") in ("SOUS_EVALUE", "SUR_EVALUE")],
    }


# ── Usage LLM (coûts tokens par projet) ─────────────────────────────────
@router.get("/{project_id}/llm-usage")
@limiter.limit("30/hour")
async def get_llm_usage(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne le résumé des tokens et coûts LLM pour la dernière analyse du projet."""
    await _get_project_or_404(project_id, org.id, db)

    result = await db.execute(
        select(ExtractionResult).where(
            ExtractionResult.project_id == project_id,
            ExtractionResult.result_type == "llm_usage",
        ).order_by(ExtractionResult.version.desc()).limit(1)
    )
    er = result.scalar_one_or_none()
    if not er or not er.payload:
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cached_tokens": 0,
            "estimated_cost_eur": 0.0,
            "steps": [],
            "message": "Aucune analyse effectuée ou données de coût non disponibles.",
        }

    payload = er.payload if isinstance(er.payload, dict) else {}
    return {
        "total_input_tokens": payload.get("total_input", 0),
        "total_output_tokens": payload.get("total_output", 0),
        "total_cached_tokens": payload.get("total_cached", 0),
        "estimated_cost_eur": payload.get("estimated_cost_eur", 0.0),
        "steps": payload.get("details", []),
        "analysis_date": er.created_at.isoformat() if er.created_at else None,
    }


# ── Sous-traitance ───────────────────────────────────────────────────────
@router.get("/{project_id}/subcontracting")
@limiter.limit("10/hour")
async def get_subcontracting(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Analyse de la stratégie de sous-traitance optimale."""
    await _get_project_or_404(project_id, org.id, db)

    cache_key = f"subcontracting:{project_id}"
    try:
        cached = get_redis().get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    from app.services.subcontracting_analyzer import analyze_subcontracting
    from app.worker.tasks import SyncSession

    sync_db = SyncSession()
    try:
        result = await analyze_subcontracting(str(project_id), sync_db)
    finally:
        sync_db.close()

    try:
        get_redis().set(cache_key, json.dumps(result, default=str), ex=3600)
    except Exception:
        pass

    return result
