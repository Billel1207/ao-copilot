"""Génération PDF d'export avec xhtml2pdf + Word avec python-docx."""
import uuid
import logging
from datetime import datetime
from io import BytesIO
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.project import AoProject
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem

EXPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #0F172A; margin: 0; padding: 0; }
  .page { padding: 30px 40px; }
  h1 { font-size: 20px; color: #1E40AF; border-bottom: 2px solid #1E40AF; padding-bottom: 8px; }
  h2 { font-size: 14px; color: #1E40AF; margin-top: 24px; }
  h3 { font-size: 12px; color: #374151; margin-top: 16px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
  .badge-red { background: #FEE2E2; color: #DC2626; }
  .badge-yellow { background: #FEF3C7; color: #D97706; }
  .badge-green { background: #DCFCE7; color: #16A34A; }
  .badge-gray { background: #F1F5F9; color: #64748B; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  th { background: #F8FAFC; font-weight: 600; text-align: left; padding: 6px 8px; border: 1px solid #E2E8F0; font-size: 10px; }
  td { padding: 6px 8px; border: 1px solid #E2E8F0; vertical-align: top; font-size: 10px; }
  tr:nth-child(even) { background: #F8FAFC; }
  .citation { font-style: italic; color: #6B7280; font-size: 9px; margin-top: 3px; }
  .risk-high { background: #FEF2F2; }
  .risk-medium { background: #FFFBEB; }
  .summary-box { background: #EFF6FF; border-left: 4px solid #1E40AF; padding: 12px 16px; margin: 12px 0; }
  .footer { text-align: center; color: #9CA3AF; font-size: 9px; margin-top: 30px; border-top: 1px solid #E2E8F0; padding-top: 8px; }
  @page { margin: 20mm; size: A4; }
</style>
</head>
<body>
<div class="page">

  <h1>AO Copilot — Rapport d'analyse</h1>
  <p style="color:#6B7280">Projet : <strong>{{ project.title }}</strong> &nbsp;|&nbsp; Acheteur : {{ project.buyer or 'N/A' }} &nbsp;|&nbsp; Statut : {{ project.status }}</p>

  <!-- RÉSUMÉ -->
  {% if summary %}
  <h2>1. Résumé exécutif</h2>
  <div class="summary-box">
    <strong>Objet :</strong> {{ summary.project_overview.scope }}<br>
    <strong>Acheteur :</strong> {{ summary.project_overview.buyer }}<br>
    <strong>Lieu :</strong> {{ summary.project_overview.location }}<br>
    <strong>Date limite :</strong> {{ summary.project_overview.deadline_submission }}<br>
    {% if summary.project_overview.estimated_budget %}<strong>Budget estimé :</strong> {{ summary.project_overview.estimated_budget }}{% endif %}
  </div>

  <h3>Points clés</h3>
  <table>
    <tr><th>Point</th><th>Valeur</th><th>Source</th></tr>
    {% for kp in summary.key_points %}
    <tr>
      <td><strong>{{ kp.label }}</strong></td>
      <td>{{ kp.value }}</td>
      <td>{% for c in kp.citations %}<span class="citation">{{ c.doc }} p.{{ c.page }}</span>{% endfor %}</td>
    </tr>
    {% endfor %}
  </table>

  <h3>Risques identifiés</h3>
  <table>
    <tr><th>Risque</th><th>Sévérité</th><th>Pourquoi</th></tr>
    {% for r in summary.risks %}
    <tr class="risk-{{ r.severity }}">
      <td>{{ r.risk }}</td>
      <td><span class="badge {% if r.severity == 'high' %}badge-red{% elif r.severity == 'medium' %}badge-yellow{% else %}badge-gray{% endif %}">{{ r.severity|upper }}</span></td>
      <td>{{ r.why }}</td>
    </tr>
    {% endfor %}
  </table>

  <h3>Actions sous 48h</h3>
  <table>
    <tr><th>Action</th><th>Responsable</th><th>Priorité</th></tr>
    {% for a in summary.actions_next_48h %}
    <tr>
      <td>{{ a.action }}</td>
      <td>{{ a.owner_role }}</td>
      <td><span class="badge {% if a.priority == 'P0' %}badge-red{% elif a.priority == 'P1' %}badge-yellow{% else %}badge-gray{% endif %}">{{ a.priority }}</span></td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  <!-- CHECKLIST -->
  {% if checklist_items %}
  <h2>2. Checklist des exigences ({{ checklist_items|length }} items)</h2>
  <table>
    <tr><th>#</th><th>Exigence</th><th>Catégorie</th><th>Criticité</th><th>Statut</th><th>À fournir</th></tr>
    {% for item in checklist_items %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ item.requirement }}
        {% for c in (item.citations or []) %}<div class="citation">{{ c.doc }} p.{{ c.page }} — "{{ c.quote[:80] }}"</div>{% endfor %}
      </td>
      <td>{{ item.category or '-' }}</td>
      <td><span class="badge {% if item.criticality == 'Éliminatoire' %}badge-red{% elif item.criticality == 'Important' %}badge-yellow{% else %}badge-gray{% endif %}">{{ item.criticality or '-' }}</span></td>
      <td><span class="badge {% if item.status == 'OK' %}badge-green{% elif item.status == 'MANQUANT' %}badge-red{% else %}badge-yellow{% endif %}">{{ item.status }}</span></td>
      <td>{{ item.what_to_provide or '-' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  <!-- CRITÈRES -->
  {% if criteria %}
  <h2>3. Critères d'attribution</h2>
  {% if criteria.evaluation.eligibility_conditions %}
  <h3>Conditions d'éligibilité</h3>
  <table>
    <tr><th>Condition</th><th>Type</th></tr>
    {% for c in criteria.evaluation.eligibility_conditions %}
    <tr>
      <td>{{ c.condition }}</td>
      <td><span class="badge {% if c.type == 'hard' %}badge-red{% else %}badge-yellow{% endif %}">{{ c.type|upper }}</span></td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
  {% if criteria.evaluation.scoring_criteria %}
  <h3>Critères de notation</h3>
  <table>
    <tr><th>Critère</th><th>Pondération</th><th>Notes</th></tr>
    {% for c in criteria.evaluation.scoring_criteria %}
    <tr>
      <td>{{ c.criterion }}</td>
      <td>{% if c.weight_percent %}{{ c.weight_percent }}%{% else %}N/S{% endif %}</td>
      <td>{{ c.notes or '-' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
  {% endif %}

  <div class="footer">Généré par AO Copilot — aocopilot.fr — {{ generated_at }}</div>
</div>
</body>
</html>
"""


def generate_export_pdf(db: Session, project_id: str) -> bytes:
    project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
    if not project:
        raise ValueError("Projet introuvable")

    summary_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="summary"
    ).order_by(ExtractionResult.version.desc()).first()

    criteria_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="criteria"
    ).order_by(ExtractionResult.version.desc()).first()

    checklist_items = db.query(ChecklistItem).filter_by(
        project_id=uuid.UUID(project_id)
    ).order_by(ChecklistItem.criticality, ChecklistItem.category).all()

    from datetime import datetime
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(EXPORT_TEMPLATE)

    try:
        html_content = template.render(
            project=project,
            summary=summary_result.payload if summary_result else None,
            checklist_items=checklist_items,
            criteria=criteria_result.payload if criteria_result else None,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
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


def generate_export_docx(db: Session, project_id: str) -> bytes:
    """Génère un rapport Word (.docx) à partir des données d'analyse.
    Requiert le plan Pro (vérifié en amont dans la route).
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from io import BytesIO
    except ImportError as e:
        raise RuntimeError("python-docx non installé. Ajoutez python-docx==1.1.0.") from e

    project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
    if not project:
        raise ValueError("Projet introuvable")

    summary_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="summary"
    ).order_by(ExtractionResult.version.desc()).first()

    criteria_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="criteria"
    ).order_by(ExtractionResult.version.desc()).first()

    checklist_items = db.query(ChecklistItem).filter_by(
        project_id=uuid.UUID(project_id)
    ).order_by(ChecklistItem.criticality, ChecklistItem.category).all()

    doc = Document()

    # ── Style global ────────────────────────────────────────────────────
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    # ── Titre ───────────────────────────────────────────────────────────
    title = doc.add_heading("AO Copilot — Rapport d'analyse", 0)
    title.runs[0].font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)

    doc.add_paragraph(
        f"Projet : {project.title}  |  Acheteur : {project.buyer or 'N/A'}  |  "
        f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ).runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # ── 1. Résumé exécutif ──────────────────────────────────────────────
    if summary_result and summary_result.payload:
        s = summary_result.payload
        po = s.get("project_overview", {})

        doc.add_heading("1. Résumé exécutif", 1)

        # Overview box
        overview_table = doc.add_table(rows=1, cols=2)
        overview_table.style = "Table Grid"
        hdr = overview_table.rows[0].cells
        hdr[0].text = "Informations marché"
        hdr[0].paragraphs[0].runs[0].bold = True
        hdr[1].text = ""

        info_pairs = [
            ("Acheteur", po.get("buyer", "—")),
            ("Type de marché", po.get("market_type", "—")),
            ("Date limite", po.get("deadline_submission", "—")),
            ("Budget estimé", po.get("estimated_budget", "Non précisé")),
            ("Lieu", po.get("location", "—")),
            ("Périmètre", po.get("scope", "—")),
        ]
        for label, value in info_pairs:
            row = overview_table.add_row().cells
            row[0].text = label
            row[0].paragraphs[0].runs[0].bold = True
            row[1].text = str(value)

        # Risques
        risks = s.get("risks", [])
        if risks:
            doc.add_heading("Risques identifiés", 2)
            risk_table = doc.add_table(rows=1, cols=3)
            risk_table.style = "Table Grid"
            hdrs = risk_table.rows[0].cells
            for i, h in enumerate(["Risque", "Sévérité", "Explication"]):
                hdrs[i].text = h
                hdrs[i].paragraphs[0].runs[0].bold = True
            for r in risks:
                row = risk_table.add_row().cells
                row[0].text = r.get("risk", "")
                row[1].text = r.get("severity", "").upper()
                row[2].text = r.get("why", "")

        # Actions 48h
        actions = s.get("actions_next_48h", [])
        if actions:
            doc.add_heading("Actions sous 48h", 2)
            act_table = doc.add_table(rows=1, cols=3)
            act_table.style = "Table Grid"
            hdrs = act_table.rows[0].cells
            for i, h in enumerate(["Action", "Responsable", "Priorité"]):
                hdrs[i].text = h
                hdrs[i].paragraphs[0].runs[0].bold = True
            for a in actions:
                row = act_table.add_row().cells
                row[0].text = a.get("action", "")
                row[1].text = a.get("owner_role", "")
                row[2].text = a.get("priority", "")

    # ── 2. Checklist ─────────────────────────────────────────────────────
    if checklist_items:
        doc.add_page_break()
        doc.add_heading(f"2. Checklist des exigences ({len(checklist_items)} items)", 1)

        cl_table = doc.add_table(rows=1, cols=5)
        cl_table.style = "Table Grid"
        hdrs = cl_table.rows[0].cells
        for i, h in enumerate(["Exigence", "Catégorie", "Criticité", "Statut", "À fournir"]):
            hdrs[i].text = h
            hdrs[i].paragraphs[0].runs[0].bold = True

        for item in checklist_items:
            row = cl_table.add_row().cells
            row[0].text = item.requirement or ""
            row[1].text = item.category or "—"
            row[2].text = item.criticality or "—"
            row[3].text = item.status or "—"
            row[4].text = item.what_to_provide or "—"

    # ── 3. Critères ──────────────────────────────────────────────────────
    if criteria_result and criteria_result.payload:
        doc.add_page_break()
        doc.add_heading("3. Critères d'attribution", 1)
        ev = criteria_result.payload.get("evaluation", {})

        elig = ev.get("eligibility_conditions", [])
        if elig:
            doc.add_heading("Conditions d'éligibilité", 2)
            e_table = doc.add_table(rows=1, cols=2)
            e_table.style = "Table Grid"
            hdrs = e_table.rows[0].cells
            for i, h in enumerate(["Condition", "Type"]):
                hdrs[i].text = h
                hdrs[i].paragraphs[0].runs[0].bold = True
            for c in elig:
                row = e_table.add_row().cells
                row[0].text = c.get("condition", "")
                row[1].text = c.get("type", "").upper()

        scoring = ev.get("scoring_criteria", [])
        if scoring:
            doc.add_heading("Critères de notation", 2)
            sc_table = doc.add_table(rows=1, cols=3)
            sc_table.style = "Table Grid"
            hdrs = sc_table.rows[0].cells
            for i, h in enumerate(["Critère", "Pondération", "Notes"]):
                hdrs[i].text = h
                hdrs[i].paragraphs[0].runs[0].bold = True
            for c in scoring:
                row = sc_table.add_row().cells
                row[0].text = c.get("criterion", "")
                w = c.get("weight_percent")
                row[1].text = f"{w}%" if w is not None else "N/S"
                row[2].text = c.get("notes") or "—"

    # ── Footer ─────────────────────────────────────────────────────────
    doc.add_paragraph()
    footer_para = doc.add_paragraph("Généré par AO Copilot — aocopilot.fr")
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.runs[0].font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)
    footer_para.runs[0].font.size = Pt(8)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_memo_technique(db: Session, project_id: str) -> bytes:
    """Génère une mémoire technique Word (.docx) pré-remplie par l'IA.
    Requiert le plan Pro (vérifié en amont dans la route).
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        from io import BytesIO
    except ImportError as e:
        raise RuntimeError("python-docx non installé. Ajoutez python-docx==1.1.0.") from e

    project = db.query(AoProject).filter_by(id=uuid.UUID(project_id)).first()
    if not project:
        raise ValueError("Projet introuvable")

    summary_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="summary"
    ).order_by(ExtractionResult.version.desc()).first()

    criteria_result = db.query(ExtractionResult).filter_by(
        project_id=uuid.UUID(project_id), result_type="criteria"
    ).order_by(ExtractionResult.version.desc()).first()

    checklist_items = db.query(ChecklistItem).filter_by(
        project_id=uuid.UUID(project_id)
    ).order_by(ChecklistItem.criticality, ChecklistItem.category).all()

    doc = Document()

    # ── Style global ────────────────────────────────────────────────────
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    # ── En-tête ──────────────────────────────────────────────────────────
    section = doc.sections[0]
    header = section.header
    header_para = header.paragraphs[0]
    header_para.text = f"{project.buyer or 'Notre Entreprise'} — Réponse à l'appel d'offres"
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if header_para.runs:
        header_para.runs[0].font.size = Pt(8)
        header_para.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # ── Pied de page avec numérotation ───────────────────────────────────
    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.add_run("Page ")
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)
    # Champ numéro de page automatique (XML Word)
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = "PAGE"
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run_xml = footer_para.add_run()
    run_xml.font.size = Pt(8)
    run_xml._r.append(fldChar_begin)
    run_xml._r.append(instrText)
    run_xml._r.append(fldChar_end)

    # ── Page de garde ────────────────────────────────────────────────────
    title_heading = doc.add_heading("MÉMOIRE TECHNIQUE", 0)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if title_heading.runs:
        title_heading.runs[0].font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)

    doc.add_paragraph()

    # Bloc informatif page de garde
    info_table = doc.add_table(rows=0, cols=2)
    info_table.style = "Table Grid"
    garde_pairs = [
        ("Marché", project.title),
        ("Acheteur public", project.buyer or "—"),
        ("Référence", project.reference or "—"),
        ("Date de remise", project.submission_deadline.strftime("%d/%m/%Y") if project.submission_deadline else "—"),
        ("Document établi le", datetime.now().strftime("%d/%m/%Y")),
    ]
    for label, value in garde_pairs:
        row = info_table.add_row().cells
        row[0].text = label
        if row[0].paragraphs[0].runs:
            row[0].paragraphs[0].runs[0].bold = True
        else:
            p = row[0].paragraphs[0]
            run = p.add_run(label)
            run.bold = True
            row[0].paragraphs[0].clear()
            row[0].paragraphs[0].add_run(label).bold = True
        row[1].text = value

    doc.add_page_break()

    # ── Données IA extraites ─────────────────────────────────────────────
    summary_payload: dict = summary_result.payload if summary_result and summary_result.payload else {}
    project_overview: dict = summary_payload.get("project_overview", {})
    key_points: list = summary_payload.get("key_points", [])
    criteria_payload: dict = criteria_result.payload if criteria_result and criteria_result.payload else {}
    evaluation: dict = criteria_payload.get("evaluation", {})
    eligibility_conditions: list = evaluation.get("eligibility_conditions", [])

    # ── Section 1 : Compréhension du besoin ──────────────────────────────
    doc.add_heading("1. Compréhension du besoin", 1)

    scope_text = project_overview.get("scope") or "Le présent marché porte sur des prestations à définir."
    market_type = project_overview.get("market_type") or project.market_type or "non précisé"
    location = project_overview.get("location") or "—"
    estimated_budget = project_overview.get("estimated_budget")

    intro_para = doc.add_paragraph()
    intro_para.add_run(
        f"Dans le cadre de la consultation lancée par {project.buyer or 'l\'acheteur public'}, "
        f"nous avons analysé en détail les documents du marché ({market_type}) "
        f"afin de formuler une réponse parfaitement adaptée aux besoins exprimés."
    )

    doc.add_paragraph()
    scope_heading = doc.add_heading("Objet et périmètre du marché", 2)

    scope_para = doc.add_paragraph(scope_text)

    if location != "—":
        doc.add_paragraph(f"Lieu d'exécution : {location}")
    if estimated_budget:
        doc.add_paragraph(f"Enveloppe budgétaire estimée : {estimated_budget}")

    if key_points:
        doc.add_heading("Points clés identifiés", 2)
        for kp in key_points:
            label = kp.get("label", "")
            value = kp.get("value", "")
            if label and value:
                p = doc.add_paragraph(style="List Bullet")
                run_label = p.add_run(f"{label} : ")
                run_label.bold = True
                p.add_run(str(value))

    doc.add_page_break()

    # ── Section 2 : Approche méthodologique ──────────────────────────────
    doc.add_heading("2. Notre approche méthodologique", 1)
    doc.add_paragraph(
        "Notre organisation a développé une approche rigoureuse et éprouvée pour répondre "
        "aux exigences de ce type de marché. Nous mettons en avant les principes suivants :"
    )

    methodologie_items = [
        ("Analyse préalable", "Étude approfondie du CCTP, du RC et des pièces contractuelles pour identifier les contraintes techniques et réglementaires."),
        ("Organisation dédiée", "Mise en place d'une équipe projet pluridisciplinaire avec un chef de projet identifié comme interlocuteur unique."),
        ("Planification rigoureuse", "Élaboration d'un planning détaillé respectant les jalons imposés par l'acheteur."),
        ("Contrôle qualité", "Processus de vérification à chaque étape pour garantir la conformité aux spécifications techniques."),
        ("Reporting régulier", "Communication proactive et transparente avec l'acheteur tout au long de l'exécution."),
    ]
    for title_item, desc in methodologie_items:
        p = doc.add_paragraph(style="List Bullet")
        run_t = p.add_run(f"{title_item} : ")
        run_t.bold = True
        p.add_run(desc)

    doc.add_paragraph()
    doc.add_paragraph(
        "[Complétez cette section avec votre méthodologie spécifique, vos process internes "
        "et toute valeur ajoutée propre à votre organisation.]"
    ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_page_break()

    # ── Section 3 : Critères de qualification ────────────────────────────
    doc.add_heading("3. Critères de qualification et conformité", 1)

    if eligibility_conditions:
        doc.add_paragraph(
            "Le tableau ci-dessous présente les conditions d'éligibilité identifiées "
            "dans les documents du marché ainsi que notre niveau de conformité :"
        )
        crit_table = doc.add_table(rows=1, cols=3)
        crit_table.style = "Table Grid"
        hdrs = crit_table.rows[0].cells
        for i, h in enumerate(["Condition d'éligibilité", "Type", "Notre conformité"]):
            hdrs[i].text = h
            if hdrs[i].paragraphs[0].runs:
                hdrs[i].paragraphs[0].runs[0].bold = True
        for cond in eligibility_conditions:
            row = crit_table.add_row().cells
            row[0].text = cond.get("condition", "—")
            row[1].text = cond.get("type", "—").upper()
            row[2].text = "[À compléter]"
    else:
        doc.add_paragraph(
            "Les conditions d'éligibilité n'ont pas encore été extraites. "
            "Complétez cette section après l'analyse IA du CCTP."
        ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_paragraph()
    doc.add_paragraph(
        "[Ajoutez ici vos certifications, agréments, références et tout justificatif prouvant votre conformité.]"
    ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_page_break()

    # ── Section 4 : Planning prévisionnel ────────────────────────────────
    doc.add_heading("4. Planning prévisionnel", 1)

    deadline_str = (
        project.submission_deadline.strftime("%d/%m/%Y")
        if project.submission_deadline else "à définir"
    )
    doc.add_paragraph(
        f"La date limite de remise des offres est fixée au {deadline_str}. "
        "Nous proposons le planning prévisionnel d'exécution suivant :"
    )

    planning_table = doc.add_table(rows=1, cols=3)
    planning_table.style = "Table Grid"
    plan_hdrs = planning_table.rows[0].cells
    for i, h in enumerate(["Phase", "Description", "Délai indicatif"]):
        plan_hdrs[i].text = h
        if plan_hdrs[i].paragraphs[0].runs:
            plan_hdrs[i].paragraphs[0].runs[0].bold = True
    planning_phases = [
        ("Phase 1 — Démarrage", "Réunion de lancement, validation des interfaces, accès au site", "J+15"),
        ("Phase 2 — Réalisation", "Exécution des prestations selon les spécifications techniques", "J+15 à J+X"),
        ("Phase 3 — Livraison", "Livraison, recette et levée de réserves", "J+X à J+X+15"),
        ("Phase 4 — Réception", "PV de réception, archivage, bilan final", "J+X+30"),
    ]
    for phase, desc, delai in planning_phases:
        row = planning_table.add_row().cells
        row[0].text = phase
        row[1].text = desc
        row[2].text = delai

    doc.add_paragraph()
    doc.add_paragraph(
        "[Adaptez ce planning aux contraintes spécifiques du marché et à votre organisation interne.]"
    ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_page_break()

    # ── Section 5 : Moyens humains et matériels ──────────────────────────
    doc.add_heading("5. Moyens humains et matériels", 1)
    doc.add_heading("5.1 Équipe dédiée", 2)

    team_table = doc.add_table(rows=1, cols=4)
    team_table.style = "Table Grid"
    team_hdrs = team_table.rows[0].cells
    for i, h in enumerate(["Fonction", "Nom / Profil", "Expérience", "Rôle dans le marché"]):
        team_hdrs[i].text = h
        if team_hdrs[i].paragraphs[0].runs:
            team_hdrs[i].paragraphs[0].runs[0].bold = True
    for _ in range(3):
        row = team_table.add_row().cells
        for cell in row:
            cell.text = "[À compléter]"

    doc.add_paragraph()
    doc.add_heading("5.2 Moyens matériels et techniques", 2)
    doc.add_paragraph(
        "[Listez ici vos équipements, outils, logiciels et tout moyen matériel "
        "que vous mobiliserez pour l'exécution du marché.]"
    ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_page_break()

    # ── Section 6 : Références ───────────────────────────────────────────
    doc.add_heading("6. Références et expériences similaires", 1)
    doc.add_paragraph(
        "Nous présentons ci-après nos principales références sur des marchés similaires, "
        "témoignant de notre capacité à répondre aux exigences du présent appel d'offres :"
    )

    ref_table = doc.add_table(rows=1, cols=4)
    ref_table.style = "Table Grid"
    ref_hdrs = ref_table.rows[0].cells
    for i, h in enumerate(["Maître d'ouvrage", "Intitulé du marché", "Montant (€ HT)", "Année"]):
        ref_hdrs[i].text = h
        if ref_hdrs[i].paragraphs[0].runs:
            ref_hdrs[i].paragraphs[0].runs[0].bold = True
    for _ in range(3):
        row = ref_table.add_row().cells
        for cell in row:
            cell.text = "[À compléter]"

    doc.add_paragraph()
    doc.add_paragraph(
        "[Ajoutez autant de références que nécessaire. "
        "Joignez les attestations de bonne exécution si demandé par le RC.]"
    ).runs[0].font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    # ── Section 7 : Checklist de conformité ─────────────────────────────
    if checklist_items:
        doc.add_page_break()
        doc.add_heading("7. Checklist de conformité DCE", 1)
        doc.add_paragraph(
            "Le tableau ci-dessous recense les exigences identifiées dans les documents "
            "du marché. Vérifiez chaque point avant soumission."
        )

        cl_table = doc.add_table(rows=1, cols=4)
        cl_table.style = "Table Grid"
        cl_hdrs = cl_table.rows[0].cells
        for i, h in enumerate(["Exigence", "Catégorie", "Criticité", "Statut"]):
            cl_hdrs[i].text = h
            if cl_hdrs[i].paragraphs[0].runs:
                cl_hdrs[i].paragraphs[0].runs[0].bold = True

        for item in checklist_items[:30]:
            row = cl_table.add_row().cells
            row[0].text = item.requirement or "—"
            row[1].text = item.category or "—"
            row[2].text = item.criticality or "—"
            row[3].text = item.status or "—"

    # ── Section 8 : Analyse des risques ───────────────────────────────
    risks = summary_payload.get("risks", [])
    if risks:
        doc.add_page_break()
        doc.add_heading("8. Analyse des risques et mesures d'atténuation", 1)
        doc.add_paragraph(
            "Les risques suivants ont été identifiés lors de l'analyse du DCE. "
            "Pour chaque risque, proposez votre mesure de mitigation."
        )

        risk_table = doc.add_table(rows=1, cols=4)
        risk_table.style = "Table Grid"
        risk_hdrs = risk_table.rows[0].cells
        for i, h in enumerate(["Risque identifié", "Sévérité", "Impact", "Mesure proposée"]):
            risk_hdrs[i].text = h
            if risk_hdrs[i].paragraphs[0].runs:
                risk_hdrs[i].paragraphs[0].runs[0].bold = True

        for risk in risks[:15]:
            row = risk_table.add_row().cells
            row[0].text = risk.get("risk", "—")
            row[1].text = risk.get("severity", "—").upper()
            row[2].text = risk.get("impact", "—")
            row[3].text = "[À compléter]"

    # ── Pied de page génération ──────────────────────────────────────────
    doc.add_paragraph()
    gen_para = doc.add_paragraph(
        f"Document généré par AO Copilot — aocopilot.fr — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    gen_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if gen_para.runs:
        gen_para.runs[0].font.size = Pt(8)
        gen_para.runs[0].font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
