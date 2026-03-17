"""Orchestration du pipeline IA complet pour un projet AO.

Sprint U — Crédibilité IA :
  - Validation Pydantic stricte de toutes les sorties LLM
  - Seuil de similarité RAG (pas d'hallucination sur contexte pauvre)
  - Vérification des citations (existence dans les chunks)
  - Score de confiance global par analyse
  - Validation cohérence enums, dates ISO, poids critères

Pipeline complet 16 étapes (parallélisé en 3 batches) :
  Batch 1 (parallel): Summary, Checklist, Criteria, Go/No-Go, Timeline
  Batch 2 (parallel): CCAP, RC, AE, CCTP, DC Check, Conflicts, Questions
  Batch 3 (sequential, dépend batch 1+2): Deadlines, Scoring, Cashflow, Subcontracting
"""
import uuid
import structlog
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SyncSessionLocal
from app.models.project import AoProject
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem
from app.models.deadline import ProjectDeadline
from app.models.document import AoDocument, DocumentPage
from app.models.company_profile import CompanyProfile
from app.services.retriever import retrieve_relevant_chunks, format_context, get_max_similarity
from app.services.llm import llm_service
from app.services.prompts import (
    build_summary_prompt, build_checklist_prompt, build_criteria_prompt,
    build_gonogo_prompt, build_deadline_prompt,
)
from app.services.gonogo_advanced import enrich_gonogo_with_profile
from app.services.language_detect import detect_project_language
from app.services.llm_validators import (
    ValidatedSummary, ValidatedChecklist, ValidatedCriteria,
    ValidatedGoNoGo, ValidatedTimeline,
    verify_citations_exist, compute_overall_confidence,
)

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DCE INCOMPLET — avertit si des documents critiques sont absents
# ═══════════════════════════════════════════════════════════════════════════════

# Documents essentiels d'un DCE complet (marchés publics français)
_CRITICAL_DOC_TYPES = {"RC", "CCTP"}           # Éliminatoire si absent
_IMPORTANT_DOC_TYPES = {"CCAP", "DPGF", "BPU"} # Fortement recommandé
_OPTIONAL_DOC_TYPES = {"AE", "ATTRI", "AUTRES"} # Optionnel selon procédure


def check_dce_completeness(db: Session, project_id: str) -> dict:
    """Vérifie la complétude du DCE avant analyse.

    Retourne un dict avec :
    - is_complete: bool — True si tous les documents critiques sont présents
    - missing_critical: list[str] — documents critiques manquants
    - missing_important: list[str] — documents recommandés manquants
    - present_types: list[str] — types de documents présents
    - warnings: list[str] — avertissements texte lisibles
    - doc_count: int — nombre total de documents
    """
    from app.models.document import AoDocument

    docs = db.query(AoDocument).filter_by(
        project_id=uuid.UUID(project_id)
    ).all()

    present_types = {d.doc_type for d in docs if d.doc_type}
    doc_count = len(docs)

    missing_critical = [t for t in _CRITICAL_DOC_TYPES if t not in present_types]
    missing_important = [t for t in _IMPORTANT_DOC_TYPES if t not in present_types]

    warnings = []
    if doc_count == 0:
        warnings.append("Aucun document uploadé — impossible de lancer l'analyse.")
    if missing_critical:
        for t in missing_critical:
            label = {"RC": "Règlement de Consultation", "CCTP": "Cahier des Clauses Techniques"}.get(t, t)
            warnings.append(f"Document critique manquant : {label} ({t}). L'analyse sera incomplète.")
    if missing_important:
        for t in missing_important:
            label = {"CCAP": "Cahier des Clauses Administratives",
                     "DPGF": "Décomposition du Prix Global et Forfaitaire",
                     "BPU": "Bordereau des Prix Unitaires"}.get(t, t)
            warnings.append(f"Document recommandé absent : {label} ({t}).")
    if doc_count == 1:
        warnings.append("Un seul document dans le DCE — les analyses croisées seront limitées.")

    return {
        "is_complete": len(missing_critical) == 0 and doc_count > 0,
        "missing_critical": missing_critical,
        "missing_important": missing_important,
        "present_types": sorted(present_types),
        "warnings": warnings,
        "doc_count": doc_count,
    }


SUMMARY_QUERY = "objet du marché acheteur pouvoir adjudicateur délai remise offres périmètre budget pénalités"
CHECKLIST_QUERY = "pièces à fournir candidature exigences DC1 DC2 assurance attestations certifications qualification"
CRITERIA_QUERY = "critères attribution notation pondération sélection éligibilité références CA qualification"
GONOGO_QUERY = "exigences techniques financières délai exécution budget garanties capacité CA qualification concurrence"
DEADLINE_QUERY = "date limite remise offres date début exécution durée marché visite site questions délai"

# Seuil minimum de similarité pour considérer le RAG comme exploitable
MIN_RAG_SIMILARITY = 0.40


def _get_project_org_id(db: Session, project_id: uuid.UUID) -> uuid.UUID | None:
    project = db.query(AoProject).filter_by(id=project_id).first()
    return project.org_id if project else None


def _report_to_sentry(exc: Exception, context: str) -> None:
    try:
        from app.config import settings
        if settings.SENTRY_DSN:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("pipeline_step", context)
                sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def _get_avg_ocr_quality(db: Session, project_id: str) -> float | None:
    """Récupère la qualité OCR moyenne des documents du projet.

    Returns:
        Score moyen 0-100, ou None si aucun document n'a de score OCR.
    """
    from app.models.document import AoDocument

    docs = db.query(AoDocument).filter_by(
        project_id=uuid.UUID(project_id),
    ).all()

    scores = [d.ocr_quality_score for d in docs if d.ocr_quality_score is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def _run_in_thread(step_fn, step_name, project_id):
    """Execute a pipeline step in its own thread with a dedicated DB session.

    Creates a fresh SQLAlchemy session, runs the step function, commits,
    and closes the session. Returns (step_name, result_dict) on success
    or (step_name, None) on failure (already logged inside step_fn).
    """
    thread_db = SyncSessionLocal()
    try:
        result = step_fn(thread_db)
        thread_db.commit()
        return (step_name, result)
    except Exception as exc:
        thread_db.rollback()
        _report_to_sentry(exc, step_name)
        logger.warning(f"[{project_id}] Erreur {step_name} dans thread (non bloquant): {exc}")
        return (step_name, None)
    finally:
        thread_db.close()


def run_full_analysis(db: Session, project_id: str) -> dict:
    """Pipeline complet parallélisé en 3 batches.

    Batch 1 (parallel, max_workers=5): summary, checklist, criteria, gonogo, timeline
    Batch 2 (parallel, max_workers=5): ccap, rc, ae, cctp, dc_check, conflicts, questions
    Batch 3 (sequential, depends on batch 1+2): deadlines, scoring, cashflow, subcontracting

    Chaque sortie LLM passe par un modèle Pydantic strict qui :
    - Rejette les dates invalides
    - Normalise les enums (GO/ATTENTION/NO-GO, Éliminatoire/Important/Info)
    - Vérifie la cohérence score↔recommendation
    - Vérifie les pondérations critères (somme ~100%)
    - Calcule un score de confiance global (avec pénalité OCR si qualité < 90)

    Each thread gets its own DB session via SyncSessionLocal to avoid
    SQLAlchemy thread-safety issues.
    """
    results = {}

    # Reset LLM usage tracking for this analysis run
    llm_service.reset_usage()

    # Détection de la langue dominante du DCE (bilingue FR/EN pour plans Europe/Business)
    detected_lang = detect_project_language(db, project_id)
    results["detected_language"] = detected_lang
    if detected_lang == "en":
        logger.info(f"[{project_id}] DCE en anglais détecté — prompts bilingues activés")

    # Récupérer la qualité OCR moyenne pour pénaliser la confiance si besoin
    avg_ocr_quality = _get_avg_ocr_quality(db, project_id)
    if avg_ocr_quality is not None:
        logger.info(f"[{project_id}] Qualité OCR moyenne du projet : {avg_ocr_quality:.1f}/100")
        if avg_ocr_quality < 70:
            logger.warning(
                f"[{project_id}] Qualité OCR faible ({avg_ocr_quality:.0f}/100) — "
                f"les scores de confiance seront pénalisés"
            )

    pid = uuid.UUID(project_id)

    # ══════════════════════════════════════════════════════════════
    # BATCH 1 — Analyses fondamentales (parallèles, max_workers=5)
    # summary, checklist, criteria, gonogo, timeline
    # ══════════════════════════════════════════════════════════════
    logger.info(f"[{project_id}] Batch 1/3 : lancement de 5 analyses fondamentales en parallèle")

    def _step_summary(thread_db):
        logger.info(f"[{project_id}] Batch 1 — résumé")
        summary_chunks = retrieve_relevant_chunks(thread_db, project_id, SUMMARY_QUERY, top_k=15)
        summary_context = format_context(summary_chunks)
        sys_p, usr_p = build_summary_prompt(summary_context, lang=detected_lang)
        summary_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["project_overview"],
            validator=ValidatedSummary,
        )
        for key in ("key_points", "risks"):
            items = summary_payload.get(key, [])
            items, _ = verify_citations_exist(items, summary_chunks)
            summary_payload[key] = items
        summary_payload["confidence_overall"] = compute_overall_confidence(
            summary_payload, summary_chunks, get_max_similarity(summary_chunks),
            ocr_quality=avg_ocr_quality,
        )
        _save_result(thread_db, project_id, "summary", summary_payload,
                     confidence=summary_payload["confidence_overall"])
        return summary_payload

    def _step_checklist(thread_db):
        logger.info(f"[{project_id}] Batch 1 — checklist")
        checklist_chunks = retrieve_relevant_chunks(thread_db, project_id, CHECKLIST_QUERY, top_k=20)
        checklist_context = format_context(checklist_chunks)
        sys_p, usr_p = build_checklist_prompt(checklist_context, lang=detected_lang)
        checklist_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["checklist"],
            validator=ValidatedChecklist,
        )
        items = checklist_payload.get("checklist", [])
        items, nb_verified = verify_citations_exist(items, checklist_chunks)
        checklist_payload["checklist"] = items
        checklist_payload["citations_verified"] = nb_verified
        checklist_payload["confidence_overall"] = compute_overall_confidence(
            checklist_payload, checklist_chunks, get_max_similarity(checklist_chunks),
            ocr_quality=avg_ocr_quality,
        )
        _save_result(thread_db, project_id, "checklist", checklist_payload,
                     confidence=checklist_payload["confidence_overall"])
        _save_checklist_items(thread_db, project_id, checklist_payload.get("checklist", []))
        return checklist_payload

    def _step_criteria(thread_db):
        logger.info(f"[{project_id}] Batch 1 — critères")
        criteria_chunks = retrieve_relevant_chunks(thread_db, project_id, CRITERIA_QUERY, top_k=15)
        criteria_context = format_context(criteria_chunks)
        sys_p, usr_p = build_criteria_prompt(criteria_context, lang=detected_lang)
        criteria_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["evaluation"],
            validator=ValidatedCriteria,
        )
        criteria_payload["confidence_overall"] = compute_overall_confidence(
            criteria_payload, criteria_chunks, get_max_similarity(criteria_chunks),
            ocr_quality=avg_ocr_quality,
        )
        _save_result(thread_db, project_id, "criteria", criteria_payload,
                     confidence=criteria_payload["confidence_overall"])
        _save_criteria_items(thread_db, project_id, criteria_payload.get("evaluation", {}))
        return criteria_payload

    def _step_gonogo(thread_db):
        logger.info(f"[{project_id}] Batch 1 — Go/No-Go")
        gonogo_chunks = retrieve_relevant_chunks(thread_db, project_id, GONOGO_QUERY, top_k=15)
        gonogo_context = format_context(gonogo_chunks)
        sys_p, usr_p = build_gonogo_prompt(gonogo_context, lang=detected_lang)
        try:
            gonogo_payload = llm_service.complete_json(
                sys_p, usr_p,
                required_keys=["score"],
                validator=ValidatedGoNoGo,
            )
        except Exception as exc:
            _report_to_sentry(exc, "gonogo")
            logger.warning(f"[{project_id}] Erreur LLM Go/No-Go (non bloquant): {exc}")
            gonogo_payload = {
                "score": 50, "recommendation": "ATTENTION",
                "strengths": [], "risks": ["Analyse incomplète — relancez"],
                "summary": "Score non disponible — relancez l'analyse.",
                "breakdown": {"technical_fit": 50, "financial_capacity": 50,
                              "timeline_feasibility": 50, "competitive_position": 50},
            }
        # Enrichissement profil entreprise (uses its own thread_db)
        try:
            company_profile_row = thread_db.query(CompanyProfile).filter_by(
                org_id=_get_project_org_id(thread_db, pid)
            ).first()
            company_profile_dict = None
            if company_profile_row:
                company_profile_dict = {
                    "revenue_eur": company_profile_row.revenue_eur,
                    "employee_count": company_profile_row.employee_count,
                    "certifications": company_profile_row.certifications or [],
                    "specialties": company_profile_row.specialties or [],
                    "regions": company_profile_row.regions or [],
                    "max_market_size_eur": company_profile_row.max_market_size_eur,
                    "assurance_rc_montant": getattr(company_profile_row, "assurance_rc_montant", None),
                    "assurance_decennale": getattr(company_profile_row, "assurance_decennale", None),
                    "marge_minimale_pct": getattr(company_profile_row, "marge_minimale_pct", None),
                    "max_projets_simultanes": getattr(company_profile_row, "max_projets_simultanes", None),
                    "projets_actifs_count": getattr(company_profile_row, "projets_actifs_count", None),
                    "partenaires_specialites": getattr(company_profile_row, "partenaires_specialites", None) or [],
                }
            # Note: summary not available yet in parallel — enrich without it
            gonogo_payload = enrich_gonogo_with_profile(
                gonogo_payload, company_profile_dict, None,
            )
        except Exception as exc:
            _report_to_sentry(exc, "gonogo_profile_enrichment")
            logger.warning(f"[{project_id}] Enrichissement profil échoué (non bloquant): {exc}")
        gonogo_payload["confidence_overall"] = compute_overall_confidence(
            gonogo_payload, gonogo_chunks, get_max_similarity(gonogo_chunks),
            ocr_quality=avg_ocr_quality,
        )
        _save_result(thread_db, project_id, "gonogo", gonogo_payload,
                     confidence=gonogo_payload.get("confidence_overall"))
        return gonogo_payload

    def _step_timeline(thread_db):
        logger.info(f"[{project_id}] Batch 1 — timeline")
        deadline_chunks = retrieve_relevant_chunks(thread_db, project_id, DEADLINE_QUERY, top_k=12)
        deadline_context = format_context(deadline_chunks)
        sys_p, usr_p = build_deadline_prompt(deadline_context, lang=detected_lang)
        try:
            timeline_payload = llm_service.complete_json(
                sys_p, usr_p,
                required_keys=["key_dates"],
                validator=ValidatedTimeline,
            )
        except Exception as exc:
            _report_to_sentry(exc, "timeline")
            logger.warning(f"[{project_id}] Erreur LLM timeline (non bloquant): {exc}")
            timeline_payload = {
                "submission_deadline": None, "execution_start": None,
                "execution_duration_months": None, "site_visit_date": None,
                "questions_deadline": None, "key_dates": [],
            }
        timeline_payload["confidence_overall"] = compute_overall_confidence(
            timeline_payload, deadline_chunks, get_max_similarity(deadline_chunks),
            ocr_quality=avg_ocr_quality,
        )
        _save_result(thread_db, project_id, "timeline", timeline_payload,
                     confidence=timeline_payload.get("confidence_overall"))
        return timeline_payload

    # Execute Batch 1 in parallel
    batch1_steps = {
        "summary": _step_summary,
        "checklist": _step_checklist,
        "criteria": _step_criteria,
        "gonogo": _step_gonogo,
        "timeline": _step_timeline,
    }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_run_in_thread, fn, name, project_id): name
            for name, fn in batch1_steps.items()
        }
        for future in as_completed(futures):
            step_name = futures[future]
            try:
                _, result = future.result()
                if result is not None:
                    results[step_name] = result
                else:
                    # For critical steps (summary, checklist, criteria), raise
                    if step_name in ("summary", "checklist", "criteria"):
                        raise RuntimeError(f"Étape critique '{step_name}' a échoué")
            except Exception as exc:
                if step_name in ("summary", "checklist", "criteria"):
                    logger.error(f"[{project_id}] Étape critique {step_name} échouée: {exc}")
                    raise
                logger.warning(f"[{project_id}] Étape {step_name} échouée (non bloquant): {exc}")

    logger.info(f"[{project_id}] Batch 1 terminé — {len([k for k in results if k != 'detected_language'])} analyses")

    # ══════════════════════════════════════════════════════════════
    # BATCH 2 — Analyses spécialisées (parallèles, max_workers=5)
    # ccap, rc, ae, cctp, dc_check, conflicts, questions
    # ══════════════════════════════════════════════════════════════
    logger.info(f"[{project_id}] Batch 2/3 : lancement de 7 analyses spécialisées en parallèle")

    def _step_ccap(thread_db):
        logger.info(f"[{project_id}] Batch 2 — CCAP")
        ccap_text = _get_doc_text_by_type(thread_db, pid, "CCAP")
        if not ccap_text:
            logger.info(f"[{project_id}] Pas de document CCAP — étape sautée")
            return None
        from app.services.ccap_analyzer import analyze_ccap_risks
        ccap_payload = analyze_ccap_risks(ccap_text, project_id=project_id)
        _save_result(thread_db, project_id, "ccap_risks", ccap_payload)
        logger.info(f"[{project_id}] CCAP : {len(ccap_payload.get('clauses_risquees', []))} clauses risquées")
        return ccap_payload

    def _step_rc(thread_db):
        logger.info(f"[{project_id}] Batch 2 — RC")
        rc_text = _get_doc_text_by_type(thread_db, pid, "RC")
        if not rc_text:
            logger.info(f"[{project_id}] Pas de document RC — étape sautée")
            return None
        from app.services.rc_analyzer import analyze_rc
        rc_payload = analyze_rc(rc_text, project_id=project_id)
        _save_result(thread_db, project_id, "rc_analysis", rc_payload)
        logger.info(f"[{project_id}] RC : procédure={rc_payload.get('procedure_type', 'N/A')}")
        return rc_payload

    def _step_ae(thread_db):
        logger.info(f"[{project_id}] Batch 2 — AE")
        ae_text = _get_doc_text_by_type(thread_db, pid, "AE")
        if not ae_text:
            logger.info(f"[{project_id}] Pas de document AE — étape sautée")
            return None
        from app.services.ae_analyzer import analyze_ae
        ae_payload = analyze_ae(ae_text, project_id=project_id)
        _save_result(thread_db, project_id, "ae_analysis", ae_payload)
        logger.info(f"[{project_id}] AE : score risque={ae_payload.get('score_risque_global', 'N/A')}")
        return ae_payload

    def _step_cctp(thread_db):
        logger.info(f"[{project_id}] Batch 2 — CCTP")
        cctp_text = _get_doc_text_by_type(thread_db, pid, "CCTP")
        if not cctp_text:
            logger.info(f"[{project_id}] Pas de document CCTP — étape sautée")
            return None
        from app.services.cctp_analyzer import analyze_cctp
        cctp_payload = analyze_cctp(cctp_text, project_id=project_id)
        _save_result(thread_db, project_id, "cctp_analysis", cctp_payload)
        logger.info(f"[{project_id}] CCTP : {cctp_payload.get('nb_exigences', 0)} exigences techniques")
        return cctp_payload

    def _step_dc_check(thread_db):
        logger.info(f"[{project_id}] Batch 2 — DC check")
        all_doc_text = _get_all_doc_text(thread_db, pid)
        if not all_doc_text:
            logger.info(f"[{project_id}] Pas de texte disponible pour DC check")
            return None
        from app.services.dc_checker import analyze_dc_requirements
        dc_payload = analyze_dc_requirements(all_doc_text, project_id=project_id)
        _save_result(thread_db, project_id, "dc_check", dc_payload)
        return dc_payload

    def _step_conflicts(thread_db):
        logger.info(f"[{project_id}] Batch 2 — conflits inter-documents")
        texts_by_type = _get_all_doc_texts_by_type(thread_db, pid)
        if len(texts_by_type) < 2:
            logger.info(f"[{project_id}] < 2 types de documents — conflits sautés")
            return None
        from app.services.conflict_detector import detect_conflicts
        conflicts_payload = detect_conflicts(texts_by_type, project_id=project_id)
        _save_result(thread_db, project_id, "conflicts", conflicts_payload)
        logger.info(f"[{project_id}] Conflits : {conflicts_payload.get('nb_total', 0)} détectés")
        return conflicts_payload

    def _step_questions(thread_db):
        logger.info(f"[{project_id}] Batch 2 — questions acheteur")
        questions_context = format_context(
            retrieve_relevant_chunks(thread_db, project_id, "ambiguïtés contradictions manques informations absentes", top_k=15)
        )
        if not questions_context:
            return None
        from app.services.questions_generator import generate_questions
        questions_payload = generate_questions(
            questions_context,
            summary_payload=results.get("summary"),
            project_id=project_id,
        )
        _save_result(thread_db, project_id, "questions", questions_payload)
        logger.info(f"[{project_id}] Questions : {questions_payload.get('question_count', 0)} générées")
        return questions_payload

    # Map step names to result keys for batch 2
    batch2_steps = {
        "ccap_risks": _step_ccap,
        "rc_analysis": _step_rc,
        "ae_analysis": _step_ae,
        "cctp_analysis": _step_cctp,
        "dc_check": _step_dc_check,
        "conflicts": _step_conflicts,
        "questions": _step_questions,
    }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_run_in_thread, fn, name, project_id): name
            for name, fn in batch2_steps.items()
        }
        for future in as_completed(futures):
            step_name = futures[future]
            try:
                _, result = future.result()
                if result is not None:
                    results[step_name] = result
            except Exception as exc:
                logger.warning(f"[{project_id}] Étape {step_name} échouée (non bloquant): {exc}")

    logger.info(f"[{project_id}] Batch 2 terminé — {len([k for k in results if k != 'detected_language'])} analyses cumulées")

    # ══════════════════════════════════════════════════════════════
    # BATCH 3 — Analyses dépendantes (séquentielles)
    # deadlines (← timeline), scoring (← criteria),
    # cashflow (← ae + timeline), subcontracting
    # ══════════════════════════════════════════════════════════════
    logger.info(f"[{project_id}] Batch 3/3 : 4 analyses dépendantes (séquentielles)")

    # ── 3a. Deadlines structurées (dépend de timeline) ──────────
    timeline_payload = results.get("timeline", {})
    if timeline_payload:
        try:
            _extract_and_save_deadlines(db, project_id, timeline_payload)
        except Exception as exc:
            _report_to_sentry(exc, "deadlines")
            logger.warning(f"[{project_id}] Erreur extraction deadlines (non bloquant): {exc}")

    # ── 3b. Scoring simulation (dépend de criteria) ─────────────
    logger.info(f"[{project_id}] Batch 3 — scoring")
    try:
        criteria_payload = results.get("criteria", {})
        if criteria_payload:
            from app.services.scoring_simulator import simulate_scoring
            company_profile_dict = _get_company_profile_dict(db, pid)
            scoring_payload = simulate_scoring(
                criteria_payload,
                company_profile=company_profile_dict,
                project_id=project_id,
            )
            _save_result(db, project_id, "scoring", scoring_payload)
            results["scoring"] = scoring_payload
            logger.info(f"[{project_id}] Scoring : note estimée {scoring_payload.get('note_globale_estimee', 'N/A')}/20")
    except Exception as exc:
        _report_to_sentry(exc, "scoring")
        logger.warning(f"[{project_id}] Erreur simulation scoring (non bloquant): {exc}")

    # ── 3c. Cashflow simulation (dépend de ae + timeline) ───────
    logger.info(f"[{project_id}] Batch 3 — trésorerie")
    try:
        ae_data = results.get("ae_analysis", {})
        timeline_data = results.get("timeline", {})
        montant_ht = _parse_montant(ae_data.get("montant_total_ht"))
        duree_mois = timeline_data.get("execution_duration_months")
        if montant_ht and montant_ht > 0 and duree_mois and duree_mois > 0:
            from app.services.cashflow_simulator import simulate_cashflow
            cashflow_payload = simulate_cashflow(
                montant_total_ht=montant_ht,
                duree_mois=int(duree_mois),
                avance_pct=ae_data.get("avance_pct", 5.0) or 5.0,
                retenue_pct=ae_data.get("retenue_garantie_pct", 5.0) or 5.0,
                delai_paiement_jours=ae_data.get("delai_paiement_jours", 30) or 30,
            )
            cashflow_payload["montant_total_ht"] = montant_ht
            cashflow_payload["duree_mois"] = int(duree_mois)
            _save_result(db, project_id, "cashflow_simulation", cashflow_payload)
            results["cashflow_simulation"] = cashflow_payload
            logger.info(f"[{project_id}] Trésorerie : BFR={cashflow_payload.get('bfr_eur', 0):.0f}€, risque={cashflow_payload.get('risk_level', 'N/A')}")
        else:
            logger.info(f"[{project_id}] Montant/durée manquants — simulation trésorerie sautée")
    except Exception as exc:
        _report_to_sentry(exc, "cashflow_simulation")
        logger.warning(f"[{project_id}] Erreur simulation trésorerie (non bloquant): {exc}")

    # ── 3d. Analyse sous-traitance ──────────────────────────────
    logger.info(f"[{project_id}] Batch 3 — sous-traitance")
    try:
        from app.services.subcontracting_analyzer import analyze_subcontracting
        subcontracting_payload = analyze_subcontracting(project_id, db)
        if subcontracting_payload and not subcontracting_payload.get("error"):
            _save_result(db, project_id, "subcontracting", subcontracting_payload,
                         confidence=subcontracting_payload.get("confidence_overall"))
            results["subcontracting"] = subcontracting_payload
            logger.info(f"[{project_id}] Sous-traitance : score risque={subcontracting_payload.get('score_risque', 'N/A')}")
        else:
            logger.info(f"[{project_id}] Sous-traitance : données insuffisantes")
    except Exception as exc:
        _report_to_sentry(exc, "subcontracting")
        logger.warning(f"[{project_id}] Erreur analyse sous-traitance (non bloquant): {exc}")

    # ── Post-pipeline: self-verification ────────────────────────────────
    try:
        from app.services.verification import verify_cross_analysis_consistency
        verification = verify_cross_analysis_consistency(project_id, results)
        _save_result(db, project_id, "verification", verification)
        results["verification"] = verification
        if verification["status"] != "verified":
            logger.warning(
                f"[{project_id}] Vérification croisée : {verification['status']} "
                f"({len(verification['issues'])} problème(s), score={verification['score']})"
            )
        else:
            logger.info(f"[{project_id}] Vérification croisée : OK (score={verification['score']})")
    except Exception as exc:
        _report_to_sentry(exc, "verification")
        logger.warning(f"[{project_id}] Erreur vérification (non bloquant): {exc}")

    # ── Post-pipeline: persist LLM usage/cost ───────────────────────────
    try:
        usage_summary = llm_service.get_usage_summary()
        if usage_summary.get("steps", 0) > 0:
            _save_result(db, project_id, "llm_usage", usage_summary)
            logger.info(
                f"[{project_id}] Coût LLM estimé : {usage_summary['estimated_cost_eur']}€ "
                f"({usage_summary['total_input']} tokens input, "
                f"{usage_summary['total_cached']} cached, "
                f"{usage_summary['steps']} étapes)"
            )
    except Exception as exc:
        logger.warning(f"[{project_id}] Erreur persist usage LLM (non bloquant): {exc}")

    db.commit()
    nb_analyses = sum(1 for k in results if k not in ("detected_language",))
    logger.info(f"[{project_id}] Pipeline complet terminé avec succès ({nb_analyses} analyses)")
    return results


def _save_result(db: Session, project_id: str, result_type: str, payload: dict,
                 confidence: float | None = None) -> None:
    existing = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type=result_type
    ).first()

    if existing:
        existing.payload = payload
        existing.model_used = llm_service.get_model_name()
        existing.created_at = datetime.now(timezone.utc)
        existing.confidence = confidence
        existing.version += 1
    else:
        result = ExtractionResult(
            project_id=uuid.UUID(project_id),
            result_type=result_type,
            payload=payload,
            model_used=llm_service.get_model_name(),
            confidence=confidence,
        )
        db.add(result)


def _save_checklist_items(db: Session, project_id: str, items: list[dict]) -> None:
    pid = uuid.UUID(project_id)
    try:
        db.query(ChecklistItem).filter_by(project_id=pid).delete()
        for item in items:
            ci = ChecklistItem(
                project_id=pid,
                category=item.get("category"),
                requirement=item.get("requirement", ""),
                criticality=item.get("criticality"),
                status=item.get("status", "MANQUANT"),
                what_to_provide=item.get("what_to_provide"),
                citations=item.get("citations", []),
                confidence=item.get("confidence"),
            )
            db.add(ci)
    except Exception:
        db.rollback()
        raise


def _save_criteria_items(db: Session, project_id: str, evaluation: dict) -> None:
    pid = uuid.UUID(project_id)
    try:
        db.query(CriteriaItem).filter_by(project_id=pid).delete()
        for cond in evaluation.get("eligibility_conditions", []):
            ci = CriteriaItem(
                project_id=pid,
                item_type="eligibility",
                criterion=cond.get("condition", ""),
                condition_type=cond.get("type"),
                citations=cond.get("citations", []),
            )
            db.add(ci)

        for criterion in evaluation.get("scoring_criteria", []):
            ci = CriteriaItem(
                project_id=pid,
                item_type="scoring",
                criterion=criterion.get("criterion", ""),
                weight_pct=criterion.get("weight_percent"),
                notes=criterion.get("notes"),
                citations=criterion.get("citations", []),
            )
            db.add(ci)
    except Exception:
        db.rollback()
        raise


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — extraction texte par type de document
# ══════════════════════════════════════════════════════════════════════════════

def _get_doc_text_by_type(db: Session, project_id: uuid.UUID, doc_type: str) -> str:
    """Récupère le texte agrégé de tous les documents d'un type donné."""
    docs = db.query(AoDocument).filter_by(
        project_id=project_id, doc_type=doc_type, status="done"
    ).all()
    if not docs:
        return ""
    parts = []
    for doc in docs:
        pages = db.query(DocumentPage).filter_by(
            document_id=doc.id
        ).order_by(DocumentPage.page_num).all()
        doc_text = "\n".join(p.raw_text for p in pages if p.raw_text)
        if doc_text.strip():
            parts.append(f"=== Document : {doc.original_name} ===\n{doc_text}")
    return "\n\n".join(parts)


def _get_all_doc_text(db: Session, project_id: uuid.UUID) -> str:
    """Récupère le texte de TOUS les documents du projet (pour DC check)."""
    docs = db.query(AoDocument).filter_by(
        project_id=project_id, status="done"
    ).all()
    parts = []
    for doc in docs:
        pages = db.query(DocumentPage).filter_by(
            document_id=doc.id
        ).order_by(DocumentPage.page_num).all()
        doc_text = "\n".join(p.raw_text for p in pages if p.raw_text)
        if doc_text.strip():
            parts.append(f"=== {doc.doc_type or 'AUTRES'} : {doc.original_name} ===\n{doc_text}")
    return "\n\n".join(parts)


def _get_all_doc_texts_by_type(db: Session, project_id: uuid.UUID) -> dict[str, str]:
    """Récupère un dict {doc_type: texte_agrégé} pour la détection de conflits."""
    docs = db.query(AoDocument).filter_by(
        project_id=project_id, status="done"
    ).all()
    texts: dict[str, list[str]] = {}
    for doc in docs:
        dtype = doc.doc_type or "AUTRES"
        pages = db.query(DocumentPage).filter_by(
            document_id=doc.id
        ).order_by(DocumentPage.page_num).all()
        doc_text = "\n".join(p.raw_text for p in pages if p.raw_text)
        if doc_text.strip():
            texts.setdefault(dtype, []).append(doc_text)
    return {dtype: "\n\n".join(parts) for dtype, parts in texts.items()}


def _get_company_profile_dict(db: Session, project_id: uuid.UUID) -> dict | None:
    """Charge le profil entreprise pour scoring/subcontracting."""
    org_id = _get_project_org_id(db, project_id)
    if not org_id:
        return None
    profile = db.query(CompanyProfile).filter_by(org_id=org_id).first()
    if not profile:
        return None
    return {
        "revenue_eur": profile.revenue_eur,
        "employee_count": profile.employee_count,
        "certifications": profile.certifications or [],
        "specialties": profile.specialties or [],
        "regions": profile.regions or [],
        "max_market_size_eur": profile.max_market_size_eur,
    }


def _parse_montant(value) -> float | None:
    """Parse un montant HT (string ou nombre) en float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # Nettoyer : "1 331 418,00 €" → 1331418.00
    import re
    cleaned = re.sub(r'[^\d,.]', '', str(value))
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


# ── Deadline type mapping ────────────────────────────────────────────────────

_DEADLINE_TYPE_MAP = {
    "submission_deadline": "remise_offres",
    "site_visit_date": "visite_site",
    "questions_deadline": "questions_acheteur",
}


def _extract_and_save_deadlines(db: Session, project_id: str, timeline_payload: dict) -> None:
    pid = uuid.UUID(project_id)
    deadlines_to_save: list[dict] = []

    for field, dtype in _DEADLINE_TYPE_MAP.items():
        raw_date = timeline_payload.get(field)
        if not raw_date:
            continue
        try:
            parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"[{project_id}] Date invalide pour {field}: {raw_date!r}")
            continue

        label_map = {
            "remise_offres": "Date limite de remise des offres",
            "visite_site": "Visite de site",
            "questions_acheteur": "Date limite des questions",
        }
        deadlines_to_save.append({
            "deadline_type": dtype,
            "label": label_map.get(dtype, dtype),
            "deadline_date": parsed,
            "is_critical": dtype == "remise_offres",
            "citation": None,
        })

    for kd in timeline_payload.get("key_dates", []):
        raw_date = kd.get("date")
        label = kd.get("label", "Échéance")
        mandatory = kd.get("mandatory", False)
        if not raw_date:
            continue
        try:
            parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        label_lower = label.lower()
        if any(k in label_lower for k in ("remise", "offre", "dépôt")):
            dtype = "remise_offres"
        elif any(k in label_lower for k in ("visite", "site")):
            dtype = "visite_site"
        elif any(k in label_lower for k in ("question", "acheteur")):
            dtype = "questions_acheteur"
        elif any(k in label_lower for k in ("résultat", "publication", "attribution")):
            dtype = "publication_resultats"
        else:
            dtype = "autre"

        deadlines_to_save.append({
            "deadline_type": dtype,
            "label": label,
            "deadline_date": parsed,
            "is_critical": mandatory or dtype == "remise_offres",
            "citation": None,
        })

    try:
        db.query(ProjectDeadline).filter_by(project_id=pid).delete()
        for d in deadlines_to_save:
            deadline = ProjectDeadline(
                project_id=pid,
                deadline_type=d["deadline_type"],
                label=d["label"],
                deadline_date=d["deadline_date"],
                is_critical=d["is_critical"],
                citation=d.get("citation"),
            )
            db.add(deadline)
    except Exception:
        db.rollback()
        raise

    logger.info(f"[{project_id}] {len(deadlines_to_save)} deadline(s) sauvegardée(s)")
