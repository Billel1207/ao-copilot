"""Helpers centralisés pour récupérer les données d'un projet pour l'export.

Factorise les queries DB communes entre generate_export_pdf, generate_export_docx
et generate_memo_technique, évitant ~200 lignes de duplication par fonction.
"""
import uuid
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem

logger = structlog.get_logger(__name__)


class DictObj:
    """Convertit un dict en objet avec accès par attribut (pour Jinja2).

    Retourne None pour les attributs manquants au lieu de lever AttributeError.
    Supporte la récursion (dicts imbriqués → DictObj imbriqués).
    """

    def __init__(self, d: dict | None):
        self._keys: set = set()
        for k, v in (d or {}).items():
            self._keys.add(k)
            if isinstance(v, list):
                setattr(self, k, [DictObj(i) if isinstance(i, dict) else i for i in v])
            elif isinstance(v, dict):
                setattr(self, k, DictObj(v))
            else:
                setattr(self, k, v)

    def __bool__(self):
        return True

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return None

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0


@dataclass
class ExportData:
    """Toutes les données nécessaires pour générer un export PDF/DOCX/Mémo."""

    project: AoProject
    documents: list[AoDocument] = field(default_factory=list)

    # Résultats d'analyse (payloads dicts)
    summary: dict | None = None
    criteria: dict | None = None
    gonogo: dict | None = None
    timeline: dict | None = None
    checklist_items: list = field(default_factory=list)
    checklist_stats: dict = field(default_factory=lambda: {
        "eliminatoire": 0, "important": 0, "info": 0, "ok": 0
    })
    confidence: float | None = None

    # Analyses spécialisées
    ccap_analysis: dict | None = None
    ccag_derogations: list | None = None
    ccap_clauses_risquees: list | None = None
    rc_analysis: dict | None = None
    ae_analysis: dict | None = None
    cctp_analysis: dict | None = None
    dc_check: dict | None = None
    conflicts: dict | None = None
    cashflow: dict | None = None
    subcontracting: dict | None = None
    questions: list | None = None
    scoring: dict | None = None
    dpgf_pricing: list | None = None
    glossaire_btp: list | None = None

    # Métadonnées calculées
    days_remaining: int | None = None
    deadline_str: str | None = None

    # DictObj pour Jinja2 (accès par attribut)
    gonogo_obj: DictObj | None = None
    timeline_obj: DictObj | None = None


def _fetch_result(db: Session, pid: uuid.UUID, result_type: str, *fallback_types: str) -> ExtractionResult | None:
    """Fetch le dernier ExtractionResult d'un type, avec fallback sur d'autres noms."""
    result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type=result_type
    ).order_by(ExtractionResult.version.desc()).first()
    if result:
        return result
    for ft in fallback_types:
        result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type=ft
        ).order_by(ExtractionResult.version.desc()).first()
        if result:
            return result
    return None


def fetch_export_data(db: Session, project_id: str) -> ExportData:
    """Récupère toutes les données pour un export (PDF, DOCX, Mémo).

    Centralise les queries DB pour éviter la duplication entre les 3 fonctions d'export.
    """
    project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
    if not project:
        raise ValueError("Projet introuvable")

    pid = uuid.UUID(project_id)

    documents = db.query(AoDocument).filter_by(project_id=pid).all()

    # ── Résultats principaux ──
    summary_r = _fetch_result(db, pid, "summary")
    criteria_r = _fetch_result(db, pid, "criteria")
    gonogo_r = _fetch_result(db, pid, "gonogo")
    timeline_r = _fetch_result(db, pid, "timeline")
    scoring_r = _fetch_result(db, pid, "scoring")

    summary = summary_r.payload if summary_r else None
    criteria = criteria_r.payload if criteria_r else None
    gonogo = gonogo_r.payload if gonogo_r else None
    timeline = timeline_r.payload if timeline_r else None
    scoring = scoring_r.payload if scoring_r else None

    # ── Checklist ──
    checklist_items = db.query(ChecklistItem).filter_by(
        project_id=pid
    ).order_by(ChecklistItem.criticality, ChecklistItem.category).all()

    checklist_stats = {"eliminatoire": 0, "important": 0, "info": 0, "ok": 0}
    for item in checklist_items:
        crit = (item.criticality or "").lower()
        status = (item.status or "").upper()
        if "liminatoire" in crit:
            checklist_stats["eliminatoire"] += 1
        elif "important" in crit:
            checklist_stats["important"] += 1
        else:
            checklist_stats["info"] += 1
        if status == "OK":
            checklist_stats["ok"] += 1

    # ── Confidence ──
    confidence = None
    if summary:
        confidence = summary.get("confidence_overall") or summary.get("confidence")

    # ── Analyses spécialisées ──
    ccap_r = _fetch_result(db, pid, "ccap_risks", "ccap")
    rc_r = _fetch_result(db, pid, "rc_analysis", "rc")
    ae_r = _fetch_result(db, pid, "ae_analysis")
    cctp_r = _fetch_result(db, pid, "cctp_analysis", "cctp")
    dc_r = _fetch_result(db, pid, "dc_check")
    conflicts_r = _fetch_result(db, pid, "conflicts")
    cashflow_r = _fetch_result(db, pid, "cashflow_simulation", "cashflow")
    subcontracting_r = _fetch_result(db, pid, "subcontracting")
    questions_r = _fetch_result(db, pid, "questions")

    ccap_analysis = ccap_r.payload if ccap_r else None
    ccag_derogations = None
    ccap_clauses_risquees = None
    if ccap_analysis:
        ccag_derogations = ccap_analysis.get("ccag_derogations") or ccap_analysis.get("derogations")
        ccap_clauses_risquees = ccap_analysis.get("clauses_risquees")

    rc_analysis = rc_r.payload if rc_r else None
    ae_analysis = ae_r.payload if ae_r else None
    cctp_analysis = cctp_r.payload if cctp_r else None
    dc_check = dc_r.payload if dc_r else None
    conflicts = conflicts_r.payload if conflicts_r else None
    cashflow = cashflow_r.payload if cashflow_r else None
    subcontracting = subcontracting_r.payload if subcontracting_r else None

    questions = None
    if questions_r and questions_r.payload:
        questions = questions_r.payload.get("questions") or questions_r.payload.get("priority_questions")

    # ── DPGF Pricing ──
    dpgf_pricing = None
    try:
        dpgf_r = _fetch_result(db, pid, "dpgf_pricing")
        if dpgf_r and dpgf_r.payload:
            dpgf_pricing = dpgf_r.payload.get("lines") or dpgf_r.payload.get("pricing_lines")
        if not dpgf_pricing:
            dpgf_extract = _fetch_result(db, pid, "dpgf_extraction")
            if dpgf_extract and dpgf_extract.payload:
                rows = dpgf_extract.payload.get("rows") or dpgf_extract.payload.get("lines") or []
                if rows:
                    from app.services.btp_pricing import check_dpgf_pricing
                    region = "france"
                    if summary:
                        loc = summary.get("project_overview", {}).get("location", "")
                        if loc:
                            region = loc.lower().replace(" ", "-")
                    dpgf_pricing = check_dpgf_pricing(rows, region=region)
    except Exception as exc:
        logger.warning(f"DPGF pricing benchmark non disponible: {exc}")

    # ── Glossaire BTP ──
    glossaire_btp = None
    try:
        from app.services.btp_knowledge import BTP_GLOSSARY
        priority_terms = [
            "RC", "CCTP", "CCAP", "DPGF", "BPU", "AE", "DCE", "CCAG", "CCAG-Travaux",
            "DC1", "DC2", "DC4", "DOE", "DIUO", "OPR", "GPA",
            "Retenue de garantie", "Caution bancaire", "Avance forfaitaire",
            "Pénalités de retard", "Révision de prix", "Intérêts moratoires",
            "Sous-traitance", "Mandataire", "Cotraitant",
            "Garantie décennale", "Garantie biennale", "RC Pro",
            "Allotissement", "Variante", "MAPA", "NF DTU",
            "PPSPS", "VRD", "BIM",
        ]
        # Format tuples (terme, definition) pour Jinja2 : {% for term, def in glossaire_btp %}
        glossaire_btp = [
            (t, BTP_GLOSSARY[t])
            for t in priority_terms if t in BTP_GLOSSARY
        ]
    except Exception:
        pass

    # ── Jours restants ──
    days_remaining = None
    deadline_str = None
    if summary:
        po = summary.get("project_overview", {})
        deadline_str = po.get("deadline_submission")
    if not deadline_str and timeline:
        deadline_str = timeline.get("submission_deadline")
    if deadline_str:
        try:
            dl = str(deadline_str)
            if "T" in dl:
                deadline_dt = datetime.fromisoformat(dl.replace("Z", "+00:00")).replace(tzinfo=None)
            else:
                deadline_dt = datetime.strptime(dl[:10], "%Y-%m-%d")
            days_remaining = (deadline_dt - datetime.now()).days
        except (ValueError, TypeError):
            pass

    return ExportData(
        project=project,
        documents=documents,
        summary=summary,
        criteria=criteria,
        gonogo=gonogo,
        timeline=timeline,
        checklist_items=checklist_items,
        checklist_stats=checklist_stats,
        confidence=confidence,
        ccap_analysis=ccap_analysis,
        ccag_derogations=ccag_derogations,
        ccap_clauses_risquees=ccap_clauses_risquees,
        rc_analysis=rc_analysis,
        ae_analysis=ae_analysis,
        cctp_analysis=cctp_analysis,
        dc_check=dc_check,
        conflicts=conflicts,
        cashflow=cashflow,
        subcontracting=subcontracting,
        questions=questions,
        scoring=scoring,
        dpgf_pricing=dpgf_pricing,
        glossaire_btp=glossaire_btp,
        days_remaining=days_remaining,
        deadline_str=deadline_str,
        gonogo_obj=DictObj(gonogo) if gonogo else None,
        timeline_obj=DictObj(timeline) if timeline else None,
    )
