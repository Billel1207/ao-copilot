"""Orchestration du pipeline IA complet pour un projet AO.

Sprint U — Crédibilité IA :
  - Validation Pydantic stricte de toutes les sorties LLM
  - Seuil de similarité RAG (pas d'hallucination sur contexte pauvre)
  - Vérification des citations (existence dans les chunks)
  - Score de confiance global par analyse
  - Validation cohérence enums, dates ISO, poids critères
"""
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.project import AoProject
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem
from app.models.deadline import ProjectDeadline
from app.models.company_profile import CompanyProfile
from app.services.retriever import retrieve_relevant_chunks, format_context, get_max_similarity
from app.services.llm import llm_service
from app.services.prompts import (
    build_summary_prompt, build_checklist_prompt, build_criteria_prompt,
    build_gonogo_prompt, build_deadline_prompt,
)
from app.services.gonogo_advanced import enrich_gonogo_with_profile
from app.services.llm_validators import (
    ValidatedSummary, ValidatedChecklist, ValidatedCriteria,
    ValidatedGoNoGo, ValidatedTimeline,
    verify_citations_exist, compute_overall_confidence,
)

logger = logging.getLogger(__name__)

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


def run_full_analysis(db: Session, project_id: str) -> dict:
    """Pipeline complet : RAG × 5 requêtes → 5 appels LLM validés → stockage.

    Chaque sortie LLM passe par un modèle Pydantic strict qui :
    - Rejette les dates invalides
    - Normalise les enums (GO/ATTENTION/NO-GO, Éliminatoire/Important/Info)
    - Vérifie la cohérence score↔recommendation
    - Vérifie les pondérations critères (somme ~100%)
    - Calcule un score de confiance global
    """
    results = {}

    # ── 1. Résumé ──────────────────────────────────────────────
    logger.info(f"[{project_id}] Étape 1/5 : génération du résumé")
    summary_chunks = retrieve_relevant_chunks(db, project_id, SUMMARY_QUERY, top_k=15)
    summary_context = format_context(summary_chunks)
    sys_p, usr_p = build_summary_prompt(summary_context)

    try:
        summary_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["project_overview"],
            validator=ValidatedSummary,
        )
    except Exception as exc:
        _report_to_sentry(exc, "summary")
        logger.error(f"[{project_id}] Erreur LLM résumé: {exc}")
        raise

    # Vérifier citations + confiance
    for key in ("key_points", "risks"):
        items = summary_payload.get(key, [])
        items, _ = verify_citations_exist(items, summary_chunks)
        summary_payload[key] = items

    summary_payload["confidence_overall"] = compute_overall_confidence(
        summary_payload, summary_chunks, get_max_similarity(summary_chunks)
    )
    _save_result(db, project_id, "summary", summary_payload,
                 confidence=summary_payload["confidence_overall"])
    results["summary"] = summary_payload

    # ── 2. Checklist ───────────────────────────────────────────
    logger.info(f"[{project_id}] Étape 2/5 : génération de la checklist")
    checklist_chunks = retrieve_relevant_chunks(db, project_id, CHECKLIST_QUERY, top_k=20)
    checklist_context = format_context(checklist_chunks)
    sys_p, usr_p = build_checklist_prompt(checklist_context)

    try:
        checklist_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["checklist"],
            validator=ValidatedChecklist,
        )
    except Exception as exc:
        _report_to_sentry(exc, "checklist")
        logger.error(f"[{project_id}] Erreur LLM checklist: {exc}")
        raise

    # Vérifier citations checklist
    items = checklist_payload.get("checklist", [])
    items, nb_verified = verify_citations_exist(items, checklist_chunks)
    checklist_payload["checklist"] = items
    checklist_payload["citations_verified"] = nb_verified

    checklist_payload["confidence_overall"] = compute_overall_confidence(
        checklist_payload, checklist_chunks, get_max_similarity(checklist_chunks)
    )
    _save_result(db, project_id, "checklist", checklist_payload,
                 confidence=checklist_payload["confidence_overall"])
    _save_checklist_items(db, project_id, checklist_payload.get("checklist", []))
    results["checklist"] = checklist_payload

    # ── 3. Critères ────────────────────────────────────────────
    logger.info(f"[{project_id}] Étape 3/5 : génération des critères")
    criteria_chunks = retrieve_relevant_chunks(db, project_id, CRITERIA_QUERY, top_k=15)
    criteria_context = format_context(criteria_chunks)
    sys_p, usr_p = build_criteria_prompt(criteria_context)

    try:
        criteria_payload = llm_service.complete_json(
            sys_p, usr_p,
            required_keys=["evaluation"],
            validator=ValidatedCriteria,
        )
    except Exception as exc:
        _report_to_sentry(exc, "criteria")
        logger.error(f"[{project_id}] Erreur LLM critères: {exc}")
        raise

    criteria_payload["confidence_overall"] = compute_overall_confidence(
        criteria_payload, criteria_chunks, get_max_similarity(criteria_chunks)
    )
    _save_result(db, project_id, "criteria", criteria_payload,
                 confidence=criteria_payload["confidence_overall"])
    _save_criteria_items(db, project_id, criteria_payload.get("evaluation", {}))
    results["criteria"] = criteria_payload

    # ── 4. Go/No-Go ────────────────────────────────────────────
    logger.info(f"[{project_id}] Étape 4/5 : calcul du score Go/No-Go")
    gonogo_chunks = retrieve_relevant_chunks(db, project_id, GONOGO_QUERY, top_k=15)
    gonogo_context = format_context(gonogo_chunks)
    sys_p, usr_p = build_gonogo_prompt(gonogo_context)

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

    # Enrichissement profil entreprise
    try:
        pid = uuid.UUID(project_id)
        company_profile_row = db.query(CompanyProfile).filter_by(
            org_id=_get_project_org_id(db, pid)
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
            }
        summary_for_match = results.get("summary")
        gonogo_payload = enrich_gonogo_with_profile(
            gonogo_payload, company_profile_dict, summary_for_match,
        )
    except Exception as exc:
        _report_to_sentry(exc, "gonogo_profile_enrichment")
        logger.warning(f"[{project_id}] Enrichissement profil échoué (non bloquant): {exc}")

    gonogo_payload["confidence_overall"] = compute_overall_confidence(
        gonogo_payload, gonogo_chunks, get_max_similarity(gonogo_chunks)
    )
    _save_result(db, project_id, "gonogo", gonogo_payload,
                 confidence=gonogo_payload.get("confidence_overall"))
    results["gonogo"] = gonogo_payload

    # ── 5. Timeline / Échéances ─────────────────────────────────
    logger.info(f"[{project_id}] Étape 5/5 : extraction des dates")
    deadline_chunks = retrieve_relevant_chunks(db, project_id, DEADLINE_QUERY, top_k=12)
    deadline_context = format_context(deadline_chunks)
    sys_p, usr_p = build_deadline_prompt(deadline_context)

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
        timeline_payload, deadline_chunks, get_max_similarity(deadline_chunks)
    )
    _save_result(db, project_id, "timeline", timeline_payload,
                 confidence=timeline_payload.get("confidence_overall"))
    results["timeline"] = timeline_payload

    # ── 6. Deadlines structurées ────────────────────────────────
    try:
        _extract_and_save_deadlines(db, project_id, timeline_payload)
    except Exception as exc:
        _report_to_sentry(exc, "deadlines")
        logger.warning(f"[{project_id}] Erreur extraction deadlines (non bloquant): {exc}")

    db.commit()
    logger.info(f"[{project_id}] Pipeline terminé avec succès (5 étapes)")
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
