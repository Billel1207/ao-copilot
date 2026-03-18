"""Génération PDF d'export avec xhtml2pdf.

Le template HTML est chargé depuis app/templates/export_template.html.
Les fonctions generate_export_docx et generate_memo_technique ont été
déplacées vers docx_exporter.py et memo_exporter.py respectivement.
"""
import os
import uuid
import structlog
from datetime import datetime
from io import BytesIO
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.core.report_theme import get_theme
from app.services.export_data import fetch_export_data, DictObj

logger = structlog.get_logger(__name__)

from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem

# Charger le template HTML depuis le fichier externe
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_TEMPLATE_PATH = os.path.join(_TEMPLATE_DIR, "export_template.html")
with open(_TEMPLATE_PATH, encoding="utf-8") as _f:
    EXPORT_TEMPLATE = _f.read()

# Garder une référence pour rétro-compatibilité (ancien EXPORT_TEMPLATE inline supprimé)
# Template HTML inline supprime — voir app/templates/export_template.html




def generate_export_pdf(db: Session, project_id: str) -> bytes:
    project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
    if not project:
        raise ValueError("Projet introuvable")

    pid = uuid.UUID(project_id)

    summary_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="summary"
    ).order_by(ExtractionResult.version.desc()).first()

    criteria_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="criteria"
    ).order_by(ExtractionResult.version.desc()).first()

    gonogo_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="gonogo"
    ).order_by(ExtractionResult.version.desc()).first()

    timeline_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="timeline"
    ).order_by(ExtractionResult.version.desc()).first()

    checklist_items = db.query(ChecklistItem).filter_by(
        project_id=pid
    ).order_by(ChecklistItem.criticality, ChecklistItem.category).all()

    # ── Compute checklist statistics ──
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

    # ── Extract confidence from summary ──
    confidence = None
    if summary_result and summary_result.payload:
        confidence = summary_result.payload.get("confidence_overall") or summary_result.payload.get("confidence")

    # ── Prepare gonogo & timeline payloads ──
    gonogo = gonogo_result.payload if gonogo_result else None
    timeline = timeline_result.payload if timeline_result else None

    # Convert dicts to object-like access for Jinja2 dot notation
    class _DictObj:
        """Allow dict.key access in Jinja2 templates.
        Returns None for missing scalar attrs, [] for missing list attrs."""
        def __init__(self, d):
            self._keys = set()
            for k, v in (d or {}).items():
                self._keys.add(k)
                if isinstance(v, list):
                    setattr(self, k, [_DictObj(i) if isinstance(i, dict) else i for i in v])
                elif isinstance(v, dict):
                    setattr(self, k, _DictObj(v))
                else:
                    setattr(self, k, v)
        def __bool__(self):
            return True
        def __getattr__(self, name):
            if name.startswith('_'):
                raise AttributeError(name)
            return None  # Return None for missing attributes instead of raising
        def __iter__(self):
            return iter([])
        def __len__(self):
            return 0

    gonogo_obj = _DictObj(gonogo) if gonogo else None
    timeline_obj = _DictObj(timeline) if timeline else None

    # ── Compute days remaining until submission deadline ──
    days_remaining = None
    deadline_str = None
    if summary_result and summary_result.payload:
        po = summary_result.payload.get("project_overview", {})
        deadline_str = po.get("deadline_submission")
    if not deadline_str and timeline:
        deadline_str = timeline.get("submission_deadline")
    if deadline_str:
        try:
            dl = deadline_str
            if 'T' in str(dl):
                deadline_dt = datetime.fromisoformat(str(dl).replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                deadline_dt = datetime.strptime(str(dl)[:10], '%Y-%m-%d')
            days_remaining = (deadline_dt - datetime.now()).days
        except (ValueError, TypeError):
            days_remaining = None

    # ── Extract scoring simulation (if available) ──
    scoring_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="scoring"
    ).order_by(ExtractionResult.version.desc()).first()
    scoring_simulation = scoring_result.payload if scoring_result else None

    # ── Extract CCAP analysis: derogations + clauses risquées (if available) ──
    # Try new naming first, fallback to old naming for legacy projects
    ccap_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="ccap_risks"
    ).order_by(ExtractionResult.version.desc()).first()
    if not ccap_result:
        ccap_result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type="ccap"
        ).order_by(ExtractionResult.version.desc()).first()
    ccag_derogations = None
    ccap_clauses_risquees = None
    if ccap_result and ccap_result.payload:
        ccag_derogations = ccap_result.payload.get("ccag_derogations") or ccap_result.payload.get("derogations")
        ccap_clauses_risquees = ccap_result.payload.get("clauses_risquees")

    # ── Extract RC analysis for fiche signalétique (if available) ──
    rc_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="rc_analysis"
    ).order_by(ExtractionResult.version.desc()).first()
    if not rc_result:
        rc_result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type="rc"
        ).order_by(ExtractionResult.version.desc()).first()
    rc_analysis = rc_result.payload if rc_result else None

    # ── Extract questions for buyer (if available) ──
    questions_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="questions"
    ).order_by(ExtractionResult.version.desc()).first()
    questions_list = None
    if questions_result and questions_result.payload:
        questions_list = questions_result.payload.get("questions") or questions_result.payload.get("priority_questions")

    # ── Extract CCTP analysis (if available) ──
    cctp_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="cctp_analysis"
    ).order_by(ExtractionResult.version.desc()).first()
    if not cctp_result:
        cctp_result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type="cctp"
        ).order_by(ExtractionResult.version.desc()).first()
    cctp_analysis = cctp_result.payload if cctp_result else None

    # ── Extract AE (Acte d'Engagement) analysis (if available) ──
    ae_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="ae_analysis"
    ).order_by(ExtractionResult.version.desc()).first()
    ae_analysis = ae_result.payload if ae_result else None

    # ── Extract DC Check (administrative documents) (if available) ──
    dc_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="dc_check"
    ).order_by(ExtractionResult.version.desc()).first()
    dc_check = dc_result.payload if dc_result else None

    # ── Extract Conflicts (cross-document contradictions) (if available) ──
    conflicts_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="conflicts"
    ).order_by(ExtractionResult.version.desc()).first()
    conflicts = conflicts_result.payload if conflicts_result else None

    # ── Extract Cashflow / BFR simulation (if available) ──
    cashflow_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="cashflow_simulation"
    ).order_by(ExtractionResult.version.desc()).first()
    if not cashflow_result:
        cashflow_result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type="cashflow"
        ).order_by(ExtractionResult.version.desc()).first()
    cashflow_data = cashflow_result.payload if cashflow_result else None

    # ── Extract Subcontracting analysis (if available) ──
    subcontracting_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="subcontracting"
    ).order_by(ExtractionResult.version.desc()).first()
    subcontracting = subcontracting_result.payload if subcontracting_result else None

    # ── DPGF Pricing benchmark (if DPGF/BPU documents exist) ──
    dpgf_pricing = None
    try:
        dpgf_result = db.query(ExtractionResult).filter_by(
            project_id=pid, result_type="dpgf_pricing"
        ).order_by(ExtractionResult.version.desc()).first()
        if dpgf_result and dpgf_result.payload:
            dpgf_pricing = dpgf_result.payload.get("lines") or dpgf_result.payload.get("pricing_lines")
        if not dpgf_pricing:
            # Try on-the-fly from DPGF extraction data
            dpgf_extract = db.query(ExtractionResult).filter_by(
                project_id=pid, result_type="dpgf_extraction"
            ).order_by(ExtractionResult.version.desc()).first()
            if dpgf_extract and dpgf_extract.payload:
                rows = dpgf_extract.payload.get("rows") or dpgf_extract.payload.get("lines") or []
                if rows:
                    from app.services.btp_pricing import check_dpgf_pricing
                    # Detect region from project location
                    region = "france"
                    if summary_result and summary_result.payload:
                        loc = summary_result.payload.get("project_overview", {}).get("location", "")
                        if loc:
                            region = loc.lower().replace(" ", "-")
                    dpgf_pricing = check_dpgf_pricing(rows, region=region)
    except Exception as exc:
        logger.warning(f"DPGF pricing benchmark non disponible: {exc}")
        dpgf_pricing = None

    # ── Build glossaire BTP (filtered to terms used in the report) ──
    glossaire_btp = None
    try:
        from app.services.btp_knowledge import BTP_GLOSSARY
        # Select key terms most likely referenced in an AO report
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
        glossaire_btp = [(t, BTP_GLOSSARY[t]) for t in priority_terms if t in BTP_GLOSSARY]
    except Exception as exc:
        logger.warning(f"Glossaire BTP non disponible: {exc}")
        glossaire_btp = None

    # ── Build documents inventory ──
    docs = db.query(AoDocument).filter_by(
        project_id=pid
    ).order_by(AoDocument.doc_type, AoDocument.original_name).all()
    documents_inventory = []
    for doc in docs:
        size_kb = doc.file_size_kb or 0
        size_display = f"{size_kb} Ko" if size_kb < 1024 else f"{size_kb / 1024:.1f} Mo"
        documents_inventory.append({
            "name": doc.original_name,
            "doc_type": doc.doc_type,
            "pages": doc.page_count or 0,
            "size_display": size_display,
            "ocr_quality": doc.ocr_quality_score,
        })

    env = Environment(loader=BaseLoader(), autoescape=True)

    # Custom Jinja2 filter to format ISO dates nicely
    def format_date_fr(value):
        """Convert ISO date string to French format: 15/04/2026 à 12h00."""
        if not value or not isinstance(value, str):
            return value or ''
        try:
            # Handle ISO datetime: 2026-04-15T12:00:00
            if 'T' in str(value):
                dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return dt.strftime('%d/%m/%Y à %Hh%M')
            # Handle ISO date: 2026-04-15
            dt = datetime.strptime(str(value)[:10], '%Y-%m-%d')
            return dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return str(value)

    env.filters['datefr'] = format_date_fr

    def safe_truncate(value, length=100, suffix='...'):
        """Safely truncate a value, handling None."""
        if not value:
            return ''
        s = str(value)
        if len(s) <= length:
            return s
        return s[:length] + suffix

    env.filters['trunc'] = safe_truncate

    template = env.from_string(EXPORT_TEMPLATE)

    # ── Génération des graphiques (graceful degradation si matplotlib absent) ──
    radar_chart_b64: str | None = None
    cashflow_chart_b64: str | None = None
    heatmap_chart_b64: str | None = None
    pricing_chart_b64: str | None = None
    try:
        from app.services.chart_generator import (
            generate_gonogo_radar,
            generate_cashflow_chart,
            generate_risk_heatmap,
            generate_pricing_benchmark_bars,
            chart_to_base64,
        )
        if gonogo:
            _dims = gonogo.get("dimension_scores") or gonogo.get("breakdown") or {}
            _score = gonogo.get("score")
            _title = project.title or "AO"
            radar_chart_b64 = chart_to_base64(
                generate_gonogo_radar(_dims if isinstance(_dims, dict) else {}, _score, _title)
            )
        if cashflow_data:
            cashflow_chart_b64 = chart_to_base64(
                generate_cashflow_chart(cashflow_data, project.title or "AO")
            )
        if conflicts:
            _conflict_list = conflicts.get("conflicts") or conflicts.get("items") or []
            heatmap_chart_b64 = chart_to_base64(
                generate_risk_heatmap(_conflict_list, project.title or "AO")
            )
        if dpgf_pricing:
            pricing_chart_b64 = chart_to_base64(
                generate_pricing_benchmark_bars(dpgf_pricing, project.title or "AO")
            )
    except Exception as _chart_err:
        logger.warning("chart_generation_skipped", error=str(_chart_err))

    try:
        html_content = template.render(
            project=project,
            summary=_DictObj(summary_result.payload) if summary_result and summary_result.payload else None,
            checklist_items=checklist_items,
            criteria=_DictObj(criteria_result.payload) if criteria_result and criteria_result.payload else None,
            gonogo=gonogo_obj,
            timeline=timeline_obj,
            checklist_stats=checklist_stats,
            confidence=confidence,
            days_remaining=days_remaining,
            scoring_simulation=_DictObj(scoring_simulation) if scoring_simulation else None,
            ccag_derogations=[_DictObj(d) for d in ccag_derogations] if ccag_derogations else None,
            ccap_clauses_risquees=[_DictObj(c) for c in ccap_clauses_risquees] if ccap_clauses_risquees else None,
            rc_analysis=_DictObj(rc_analysis) if rc_analysis else None,
            questions_list=[_DictObj(q) if isinstance(q, dict) else q for q in questions_list] if questions_list else None,
            documents_inventory=[_DictObj(d) for d in documents_inventory] if documents_inventory else None,
            cctp_analysis=_DictObj(cctp_analysis) if cctp_analysis else None,
            cashflow_data=_DictObj(cashflow_data) if cashflow_data else None,
            subcontracting=_DictObj(subcontracting) if subcontracting else None,
            ae_analysis=_DictObj(ae_analysis) if ae_analysis else None,
            dc_check=_DictObj(dc_check) if dc_check else None,
            conflicts=_DictObj(conflicts) if conflicts else None,
            dpgf_pricing=[_DictObj(line) for line in dpgf_pricing] if dpgf_pricing else None,
            glossaire_btp=glossaire_btp,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            generation_date=datetime.now().strftime("%d/%m/%Y"),
            theme=get_theme(),
            radar_chart_b64=radar_chart_b64,
            cashflow_chart_b64=cashflow_chart_b64,
            heatmap_chart_b64=heatmap_chart_b64,
            pricing_chart_b64=pricing_chart_b64,
        )
    except Exception as exc:
        logger.error(f"Erreur rendu template Jinja2 pour project {project_id}: {exc}")
        raise RuntimeError(f"Erreur de génération du template PDF: {exc}") from exc

    try:
        from xhtml2pdf import pisa
        output = BytesIO()
        result = pisa.CreatePDF(html_content, dest=output, encoding="utf-8")
        if result.err:
            raise RuntimeError(f"xhtml2pdf errors: {result.err}")
        pdf_bytes = output.getvalue()
    except Exception as exc:
        logger.error(f"Erreur xhtml2pdf pour project {project_id}: {exc}")
        raise RuntimeError(f"Erreur de génération PDF: {exc}") from exc

    return pdf_bytes



# ── Re-exports pour retro-compatibilite ──────────────────────────────────
# Les fonctions ci-dessous ont ete deplacees dans des modules dedies.
# Ces imports permettent aux anciens appels de continuer a fonctionner.
from app.services.docx_exporter import generate_export_docx  # noqa: F401
from app.services.memo_exporter import generate_memo_technique  # noqa: F401
