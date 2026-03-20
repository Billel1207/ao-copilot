"""Génération PDF d'export avec xhtml2pdf.

Le template HTML est chargé depuis app/templates/export_template.html.
Les données sont centralisées dans export_data.py (fetch_export_data).
Les fonctions generate_export_docx et generate_memo_technique ont été
déplacées vers docx_exporter.py et memo_exporter.py respectivement.
"""
import os
import structlog
from datetime import datetime
from io import BytesIO
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.core.report_theme import get_theme
from app.services.export_data import fetch_export_data, DictObj

logger = structlog.get_logger(__name__)

# Charger le template HTML depuis le fichier externe
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_TEMPLATE_PATH = os.path.join(_TEMPLATE_DIR, "export_template.html")
with open(_TEMPLATE_PATH, encoding="utf-8") as _f:
    EXPORT_TEMPLATE = _f.read()


def _format_date_fr(value):
    """Convert ISO date string to French format: 15/04/2026 à 12h00."""
    if not value or not isinstance(value, str):
        return value or ''
    try:
        if 'T' in str(value):
            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y à %Hh%M')
        dt = datetime.strptime(str(value)[:10], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return str(value)


def _safe_truncate(value, length=100, suffix='...'):
    """Safely truncate a value, handling None."""
    if not value:
        return ''
    s = str(value)
    return s if len(s) <= length else s[:length] + suffix


def _build_documents_inventory(documents) -> list[dict]:
    """Construit l'inventaire des documents pour le template."""
    inventory = []
    for doc in documents:
        size_kb = doc.file_size_kb or 0
        size_display = f"{size_kb} Ko" if size_kb < 1024 else f"{size_kb / 1024:.1f} Mo"
        inventory.append({
            "name": doc.original_name,
            "doc_type": doc.doc_type,
            "pages": doc.page_count or 0,
            "size_display": size_display,
            "ocr_quality": doc.ocr_quality_score,
        })
    return inventory


def _generate_charts(data) -> dict[str, str | None]:
    """Génère les graphiques en base64 (graceful degradation si matplotlib absent)."""
    charts: dict[str, str | None] = {
        "radar_chart_b64": None,
        "cashflow_chart_b64": None,
        "heatmap_chart_b64": None,
        "pricing_chart_b64": None,
    }
    try:
        from app.services.chart_generator import (
            generate_gonogo_radar,
            generate_cashflow_chart,
            generate_risk_heatmap,
            generate_pricing_benchmark_bars,
            chart_to_base64,
        )
        title = data.project.title or "AO"

        if data.gonogo:
            dims = data.gonogo.get("dimension_scores") or data.gonogo.get("breakdown") or {}
            score = data.gonogo.get("score")
            charts["radar_chart_b64"] = chart_to_base64(
                generate_gonogo_radar(dims if isinstance(dims, dict) else {}, score, title)
            )
        if data.cashflow:
            charts["cashflow_chart_b64"] = chart_to_base64(
                generate_cashflow_chart(data.cashflow, title)
            )
        if data.conflicts:
            conflict_list = data.conflicts.get("conflicts") or data.conflicts.get("items") or []
            charts["heatmap_chart_b64"] = chart_to_base64(
                generate_risk_heatmap(conflict_list, title)
            )
        if data.dpgf_pricing:
            charts["pricing_chart_b64"] = chart_to_base64(
                generate_pricing_benchmark_bars(data.dpgf_pricing, title)
            )
    except Exception as err:
        logger.warning("chart_generation_skipped", error=str(err))

    return charts


def generate_export_pdf(db: Session, project_id: str) -> bytes:
    """Génère le rapport PDF complet d'analyse DCE.

    Utilise fetch_export_data() pour centraliser les queries DB,
    puis rend le template HTML via Jinja2 et le convertit en PDF via xhtml2pdf.
    """
    # ── Récupérer toutes les données via le helper centralisé ──
    data = fetch_export_data(db, project_id)

    # ── Inventaire documents ──
    documents_inventory = _build_documents_inventory(data.documents)

    # ── Jinja2 environment ──
    env = Environment(loader=BaseLoader(), autoescape=True)
    env.filters['datefr'] = _format_date_fr
    env.filters['trunc'] = _safe_truncate
    template = env.from_string(EXPORT_TEMPLATE)

    # ── Graphiques ──
    charts = _generate_charts(data)

    # ── Rendu template ──
    try:
        html_content = template.render(
            project=data.project,
            summary=DictObj(data.summary) if data.summary else None,
            checklist_items=data.checklist_items,
            criteria=DictObj(data.criteria) if data.criteria else None,
            gonogo=data.gonogo_obj,
            timeline=data.timeline_obj,
            checklist_stats=data.checklist_stats,
            confidence=data.confidence,
            days_remaining=data.days_remaining,
            scoring_simulation=DictObj(data.scoring) if data.scoring else None,
            ccag_derogations=[DictObj(d) if isinstance(d, dict) else DictObj({}) for d in data.ccag_derogations] if isinstance(data.ccag_derogations, list) and data.ccag_derogations else None,
            ccap_clauses_risquees=[DictObj(c) if isinstance(c, dict) else DictObj({}) for c in data.ccap_clauses_risquees] if isinstance(data.ccap_clauses_risquees, list) and data.ccap_clauses_risquees else None,
            rc_analysis=DictObj(data.rc_analysis) if data.rc_analysis else None,
            questions_list=[DictObj(q) if isinstance(q, dict) else q for q in data.questions] if data.questions else None,
            documents_inventory=[DictObj(d) for d in documents_inventory] if documents_inventory else None,
            cctp_analysis=DictObj(data.cctp_analysis) if data.cctp_analysis else None,
            cashflow_data=DictObj(data.cashflow) if data.cashflow else None,
            subcontracting=DictObj(data.subcontracting) if data.subcontracting else None,
            ae_analysis=DictObj(data.ae_analysis) if data.ae_analysis else None,
            dc_check=DictObj(data.dc_check) if data.dc_check else None,
            conflicts=DictObj(data.conflicts) if data.conflicts else None,
            dpgf_pricing=[DictObj(line) if isinstance(line, dict) else DictObj({}) for line in data.dpgf_pricing] if isinstance(data.dpgf_pricing, list) and data.dpgf_pricing else None,
            glossaire_btp=data.glossaire_btp,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            generation_date=datetime.now().strftime("%d/%m/%Y"),
            theme=get_theme(),
            **charts,
        )
    except Exception as exc:
        logger.error("pdf_template_render_error", project_id=project_id, error=str(exc))
        raise RuntimeError(f"Erreur de génération du template PDF: {exc}") from exc

    # ── Conversion HTML → PDF ──
    try:
        from xhtml2pdf import pisa
        output = BytesIO()
        result = pisa.CreatePDF(html_content, dest=output, encoding="utf-8")
        if result.err:
            logger.warning("xhtml2pdf_warnings", count=result.err, project_id=project_id)
        return output.getvalue()
    except Exception as exc:
        logger.error("pdf_generation_error", project_id=project_id, error=str(exc))
        raise RuntimeError(f"Erreur de génération PDF: {exc}") from exc


# ── Re-exports pour retro-compatibilite ──────────────────────────────────
from app.services.docx_exporter import generate_export_docx  # noqa: F401
from app.services.memo_exporter import generate_memo_technique  # noqa: F401
