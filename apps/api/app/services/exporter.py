"""Génération PDF d'export avec xhtml2pdf + Word avec python-docx."""
import uuid
import structlog
from datetime import datetime
from io import BytesIO
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem

EXPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10px; color: #0F172A; margin: 0; padding: 0; }
  .page { padding: 25px 35px; }
  h1 { font-size: 22px; color: #1E40AF; border-bottom: 3px solid #1E40AF; padding-bottom: 8px; margin-top: 0; }
  h2 { font-size: 14px; color: #1E40AF; margin-top: 28px; border-bottom: 1px solid #CBD5E1; padding-bottom: 4px; }
  h3 { font-size: 11px; color: #374151; margin-top: 14px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: bold; }
  .badge-red { background: #FEE2E2; color: #DC2626; }
  .badge-yellow { background: #FEF3C7; color: #D97706; }
  .badge-green { background: #DCFCE7; color: #16A34A; }
  .badge-blue { background: #DBEAFE; color: #1D4ED8; }
  .badge-gray { background: #F1F5F9; color: #64748B; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th { background: #1E293B; color: white; font-weight: 600; text-align: left; padding: 6px 8px; border: 1px solid #334155; font-size: 9px; }
  td { padding: 5px 8px; border: 1px solid #E2E8F0; vertical-align: top; font-size: 9px; }
  tr:nth-child(even) { background: #F8FAFC; }
  .citation { font-style: italic; color: #6B7280; font-size: 8px; margin-top: 2px; }
  .risk-high { background: #FEF2F2; }
  .risk-medium { background: #FFFBEB; }
  .summary-box { background: #EFF6FF; border-left: 4px solid #1E40AF; padding: 10px 14px; margin: 10px 0; }
  .gonogo-box { padding: 16px; margin: 10px 0; text-align: center; border-radius: 6px; }
  .gonogo-go { background: #DCFCE7; border: 2px solid #16A34A; }
  .gonogo-attention { background: #FEF3C7; border: 2px solid #D97706; }
  .gonogo-nogo { background: #FEE2E2; border: 2px solid #DC2626; }
  .gonogo-score { font-size: 28px; font-weight: bold; }
  .gonogo-label { font-size: 14px; font-weight: bold; margin-top: 4px; }
  .stat-grid { display: table; width: 100%; margin: 10px 0; }
  .stat-cell { display: table-cell; text-align: center; padding: 10px; border: 1px solid #E2E8F0; width: 25%; }
  .stat-number { font-size: 20px; font-weight: bold; color: #1E40AF; }
  .stat-label { font-size: 9px; color: #64748B; margin-top: 2px; }
  .confidence-bar { background: #E2E8F0; height: 8px; border-radius: 4px; margin-top: 4px; }
  .confidence-fill { height: 8px; border-radius: 4px; }
  .cover-page { text-align: center; padding-top: 120px; }
  .cover-title { font-size: 28px; color: #1E40AF; font-weight: bold; margin-bottom: 8px; }
  .cover-subtitle { font-size: 16px; color: #374151; margin-bottom: 40px; }
  .cover-info { font-size: 12px; color: #64748B; margin: 6px 0; }
  .cover-badge { display: inline-block; padding: 6px 20px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-top: 20px; }
  .disclaimer { background: #FEF3C7; border: 1px solid #F59E0B; padding: 8px 12px; font-size: 8px; color: #92400E; margin-top: 20px; border-radius: 4px; }
  .footer { text-align: center; color: #9CA3AF; font-size: 8px; margin-top: 20px; border-top: 1px solid #E2E8F0; padding-top: 6px; }
  .page-break { page-break-before: always; }
  .toc { margin: 20px 0; }
  .toc-item { padding: 4px 0; border-bottom: 1px dotted #CBD5E1; font-size: 10px; }
  .toc-item strong { color: #1E40AF; }
  .financial-box { background: #F0FDF4; border: 1px solid #86EFAC; padding: 10px 14px; margin: 10px 0; border-radius: 4px; }
  .warning-box { background: #FEF2F2; border: 1px solid #FECACA; padding: 8px 12px; font-size: 9px; color: #991B1B; margin: 8px 0; border-radius: 4px; }
  .info-box { background: #EFF6FF; border: 1px solid #BFDBFE; padding: 8px 12px; font-size: 9px; color: #1E40AF; margin: 8px 0; border-radius: 4px; }
  @page { margin: 18mm; size: A4; }
</style>
</head>
<body>

<!-- ═══════════ PAGE DE COUVERTURE ═══════════ -->
<div class="page cover-page">
  <div style="font-size: 14px; color: #64748B; letter-spacing: 2px;">RAPPORT D'ANALYSE DCE</div>
  <div class="cover-title">{{ project.title }}</div>
  <div class="cover-subtitle">{{ project.buyer or 'Acheteur public' }}</div>

  <div style="margin-top: 40px;">
    <div class="cover-info"><strong>Référence :</strong> {{ project.reference or 'N/A' }}</div>
    {% if summary and summary.project_overview.deadline_submission %}
    <div class="cover-info"><strong>Date limite :</strong> {{ summary.project_overview.deadline_submission|datefr }}</div>
    {% endif %}
    {% if summary and summary.project_overview.estimated_budget %}
    <div class="cover-info"><strong>Budget estimé :</strong> {{ summary.project_overview.estimated_budget }}</div>
    {% endif %}
    <div class="cover-info"><strong>Lieu :</strong> {{ summary.project_overview.location if summary else 'N/A' }}</div>
  </div>

  {% if days_remaining is not none %}
  <div style="margin-top: 30px;">
    <div style="display: inline-block; padding: 12px 28px; border-radius: 8px; font-size: 18px; font-weight: bold;
      {% if days_remaining <= 3 %}background: #FEE2E2; color: #DC2626; border: 2px solid #DC2626;
      {% elif days_remaining <= 7 %}background: #FEF3C7; color: #D97706; border: 2px solid #D97706;
      {% elif days_remaining <= 14 %}background: #DBEAFE; color: #1D4ED8; border: 2px solid #1D4ED8;
      {% else %}background: #DCFCE7; color: #16A34A; border: 2px solid #16A34A;{% endif %}">
      {% if days_remaining < 0 %}EXPIRÉ (J{{ days_remaining }})
      {% elif days_remaining == 0 %}DERNIER JOUR (J-0)
      {% else %}J-{{ days_remaining }}{% endif %}
    </div>
    {% if days_remaining >= 0 %}
    <div class="cover-info" style="margin-top: 6px;">{{ days_remaining }} jour{{ 's' if days_remaining > 1 else '' }} restant{{ 's' if days_remaining > 1 else '' }} avant la date limite de remise</div>
    {% else %}
    <div class="cover-info" style="margin-top: 6px; color: #DC2626;">Date limite dépassée depuis {{ -days_remaining }} jour{{ 's' if -days_remaining > 1 else '' }}</div>
    {% endif %}
  </div>
  {% endif %}

  {% if gonogo %}
  <div style="margin-top: 20px;">
    {% set reco = gonogo.recommendation|upper if gonogo.recommendation else 'ATTENTION' %}
    <div class="cover-badge {% if reco == 'GO' %}badge-green{% elif reco == 'NO-GO' %}badge-red{% else %}badge-yellow{% endif %}" style="font-size: 16px; padding: 10px 30px;">
      RECOMMANDATION : {{ reco }}
    </div>
    <div class="cover-info" style="margin-top: 8px;">Score Go/No-Go : <strong>{{ gonogo.score }}/100</strong></div>
  </div>
  {% endif %}

  <div style="margin-top: 40px; color: #9CA3AF; font-size: 10px;">
    Document généré le {{ generated_at }}<br>
    Confiance IA : {{ "%.0f"|format(confidence * 100) if confidence else 'N/A' }}%
  </div>
</div>

<!-- ═══════════ SOMMAIRE ═══════════ -->
<div class="page page-break">
  <h1>Sommaire</h1>
  <div class="toc">
    <div class="toc-item"><strong>1.</strong> Synthese decisionnelle — Recommandation Go/No-Go et indicateurs cles</div>
    {% if summary %}
    <div class="toc-item"><strong>2.</strong> Resume executif — Objet du marche, points cles extraits</div>
    <div class="toc-item"><strong>3.</strong> Analyse des risques — {{ summary.risks|length }} risques identifies et plan d'actions 48h</div>
    {% endif %}
    {% if timeline %}
    <div class="toc-item"><strong>4.</strong> Calendrier et dates cles — Echeances de soumission et d'execution</div>
    {% endif %}
    {% if checklist_items %}
    <div class="toc-item"><strong>5.</strong> Checklist de conformite — {{ checklist_items|length }} exigences ({{ checklist_stats.eliminatoire }} eliminatoires)</div>
    {% endif %}
    {% if criteria %}
    <div class="toc-item"><strong>6.</strong> Criteres d'attribution — Conditions d'eligibilite et grille de notation</div>
    {% endif %}
    {% if scoring_simulation %}
    <div class="toc-item"><strong>6b.</strong> Simulation note acheteur — Note estimee {{ "%.1f"|format(scoring_simulation.total_score) }}/20 et leviers</div>
    {% endif %}
    {% if ccag_derogations %}
    <div class="toc-item"><strong>6c.</strong> Derogations CCAG-Travaux 2021 — {{ ccag_derogations|length }} derogations detectees</div>
    {% endif %}
    {% if rc_analysis %}
    <div class="toc-item"><strong>2b.</strong> Fiche signaletique du marche — Procedure, allotissement, groupement, CCAG</div>
    {% endif %}
    <div class="toc-item"><strong>5b.</strong> Documents prioritaires a preparer — Liste des pieces eliminatoires manquantes</div>
    <div class="toc-item"><strong>7.</strong> Synthese financiere — Montants, avance, penalites, revision des prix</div>
    {% if questions_list %}
    <div class="toc-item"><strong>8.</strong> Questions prioritaires pour l'acheteur — {{ questions_list|length }} questions a poser</div>
    {% endif %}
    {% if documents_inventory %}
    <div class="toc-item"><strong>A1.</strong> Inventaire des documents — {{ documents_inventory|length }} pieces DCE analysees</div>
    {% endif %}
    <div class="toc-item"><strong>A.</strong> Avertissement IA et mentions legales</div>
  </div>

  <div class="info-box">
    <strong>Mode d'emploi :</strong> Ce rapport est concu pour une lecture en 3 niveaux :<br>
    - <strong>5 minutes</strong> : Page de couverture + Synthese decisionnelle (pages 1-2)<br>
    - <strong>15 minutes</strong> : + Resume executif + Risques + Calendrier<br>
    - <strong>30 minutes</strong> : Rapport complet avec checklist et criteres detailles
  </div>
</div>

<!-- ═══════════ SYNTHÈSE DÉCISIONNELLE (1 page) ═══════════ -->
<div class="page page-break">
  <h1>1. Synthèse décisionnelle</h1>
  <p style="color: #64748B; font-size: 9px;">Vue d'ensemble en 1 page pour les décideurs (DG, Directeur commercial, Responsable AO)</p>

  <!-- Score Go/No-Go -->
  {% if gonogo %}
  {% set reco = gonogo.recommendation|upper if gonogo.recommendation else 'ATTENTION' %}
  <div class="gonogo-box {% if reco == 'GO' %}gonogo-go{% elif reco == 'NO-GO' %}gonogo-nogo{% else %}gonogo-attention{% endif %}">
    <div class="gonogo-score">{{ gonogo.score }}/100</div>
    <div class="gonogo-label">{{ reco }}</div>
    <div style="font-size: 10px; margin-top: 4px;">{{ gonogo.summary }}</div>
  </div>
  {% endif %}

  <!-- Indicateurs clés -->
  <div class="stat-grid">
    <div class="stat-cell">
      <div class="stat-number">{{ checklist_stats.eliminatoire }}</div>
      <div class="stat-label">Éliminatoires</div>
    </div>
    <div class="stat-cell">
      <div class="stat-number">{{ checklist_stats.important }}</div>
      <div class="stat-label">Importants</div>
    </div>
    <div class="stat-cell">
      <div class="stat-number">{{ summary.risks|length if summary else 0 }}</div>
      <div class="stat-label">Risques identifiés</div>
    </div>
    <div class="stat-cell">
      <div class="stat-number">{{ summary.actions_next_48h|length if summary else 0 }}</div>
      <div class="stat-label">Actions à mener</div>
    </div>
  </div>

  <!-- Top 3 risques -->
  {% if summary and summary.risks %}
  <h3>Top 3 risques critiques</h3>
  <table>
    <tr><th>Risque</th><th>Sévérité</th><th>Impact</th></tr>
    {% for r in summary.risks[:3] %}
    <tr class="risk-{{ r.severity }}">
      <td><strong>{{ r.risk }}</strong></td>
      <td><span class="badge {% if r.severity == 'high' %}badge-red{% elif r.severity == 'medium' %}badge-yellow{% else %}badge-gray{% endif %}">{{ r.severity|upper }}</span></td>
      <td>{{ r.why[:120] }}{% if r.why|length > 120 %}...{% endif %}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  <!-- Forces et faiblesses Go/No-Go -->
  {% if gonogo and (gonogo.strengths or gonogo.risks) %}
  <div style="display: table; width: 100%; margin-top: 12px;">
    <div style="display: table-cell; width: 48%; vertical-align: top;">
      <h3 style="color: #16A34A;">Forces</h3>
      {% for s in gonogo.strengths[:3] %}<div style="margin: 3px 0; font-size: 9px;">+ {{ s }}</div>{% endfor %}
    </div>
    <div style="display: table-cell; width: 4%;"></div>
    <div style="display: table-cell; width: 48%; vertical-align: top;">
      <h3 style="color: #DC2626;">Points de vigilance</h3>
      {% for r in gonogo.risks[:3] %}<div style="margin: 3px 0; font-size: 9px;">- {{ r }}</div>{% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Dimensions Go/No-Go -->
  {% if gonogo and gonogo.breakdown %}
  <h3>Scores par dimension</h3>
  <table>
    <tr><th style="width:50%">Dimension</th><th style="width:20%">Score</th><th style="width:30%">Niveau</th></tr>
    {% for dim_name, dim_score in [('Adéquation technique', gonogo.breakdown.technical_fit), ('Capacité financière', gonogo.breakdown.financial_capacity), ('Faisabilité planning', gonogo.breakdown.timeline_feasibility), ('Position concurrentielle', gonogo.breakdown.competitive_position)] %}
    {% if dim_score is not none %}
    <tr>
      <td>{{ dim_name }}</td>
      <td><strong>{{ dim_score }}/100</strong></td>
      <td><span class="badge {% if dim_score >= 70 %}badge-green{% elif dim_score >= 50 %}badge-yellow{% else %}badge-red{% endif %}">{% if dim_score >= 70 %}BON{% elif dim_score >= 50 %}MOYEN{% else %}FAIBLE{% endif %}</span></td>
    </tr>
    {% endif %}
    {% endfor %}
  </table>
  {% endif %}

  <!-- Actions P0 -->
  {% if summary and summary.actions_next_48h %}
  <h3>Actions prioritaires P0</h3>
  <table>
    <tr><th>Action</th><th>Responsable</th></tr>
    {% for a in summary.actions_next_48h if a.priority == 'P0' %}
    <tr>
      <td>{{ a.action[:100] }}{% if a.action|length > 100 %}...{% endif %}</td>
      <td>{{ a.owner_role }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  <!-- Confiance IA -->
  {% if confidence %}
  <div style="margin-top: 12px;">
    <span style="font-size: 9px; color: #64748B;">Indice de confiance IA : {{ "%.0f"|format(confidence * 100) }}%</span>
    <div class="confidence-bar">
      <div class="confidence-fill" style="width: {{ "%.0f"|format(confidence * 100) }}%; background: {% if confidence >= 0.8 %}#16A34A{% elif confidence >= 0.6 %}#D97706{% else %}#DC2626{% endif %};"></div>
    </div>
  </div>
  {% endif %}
</div>

<!-- ═══════════ RÉSUMÉ EXÉCUTIF ═══════════ -->
{% if summary %}
<div class="page page-break">
  <h1>2. Résumé exécutif</h1>

  <div class="summary-box">
    <strong>Objet :</strong> {{ summary.project_overview.scope }}<br>
    <strong>Acheteur :</strong> {{ summary.project_overview.buyer }}<br>
    <strong>Lieu :</strong> {{ summary.project_overview.location }}<br>
    <strong>Date limite :</strong> {{ summary.project_overview.deadline_submission }}<br>
    {% if summary.project_overview.estimated_budget %}<strong>Budget estimé :</strong> {{ summary.project_overview.estimated_budget }}<br>{% endif %}
    {% if summary.project_overview.market_type %}<strong>Type de marché :</strong> {{ summary.project_overview.market_type }}{% endif %}
  </div>

  <h3>Points clés extraits du DCE</h3>
  <table>
    <tr><th style="width:25%">Point</th><th style="width:50%">Valeur</th><th style="width:25%">Source</th></tr>
    {% for kp in summary.key_points %}
    <tr>
      <td><strong>{{ kp.label }}</strong></td>
      <td>{{ kp.value }}</td>
      <td>{% for c in kp.citations %}<span class="citation">{{ c.doc }} p.{{ c.page }}</span>{% endfor %}</td>
    </tr>
    {% endfor %}
  </table>
</div>

<!-- ═══════════ RISQUES & ACTIONS ═══════════ -->
<div class="page page-break">
  <h1>3. Analyse des risques</h1>

  <h3>Risques identifiés ({{ summary.risks|length }})</h3>
  <table>
    <tr><th style="width:30%">Risque</th><th style="width:10%">Sévérité</th><th style="width:60%">Analyse</th></tr>
    {% for r in summary.risks %}
    <tr class="risk-{{ r.severity }}">
      <td><strong>{{ r.risk }}</strong></td>
      <td><span class="badge {% if r.severity == 'high' %}badge-red{% elif r.severity == 'medium' %}badge-yellow{% else %}badge-gray{% endif %}">{{ r.severity|upper }}</span></td>
      <td>{{ r.why }}</td>
    </tr>
    {% endfor %}
  </table>

  <h3>Plan d'actions sous 48h ({{ summary.actions_next_48h|length }} actions)</h3>
  <table>
    <tr><th style="width:50%">Action</th><th style="width:30%">Responsable</th><th style="width:10%">Priorité</th></tr>
    {% for a in summary.actions_next_48h %}
    <tr>
      <td>{{ a.action }}</td>
      <td>{{ a.owner_role }}</td>
      <td><span class="badge {% if a.priority == 'P0' %}badge-red{% elif a.priority == 'P1' %}badge-yellow{% else %}badge-gray{% endif %}">{{ a.priority }}</span></td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

<!-- ═══════════ DATES CLÉS ═══════════ -->
{% if timeline %}
<div class="page page-break">
  <h1>4. Calendrier et dates clés</h1>
  <table>
    <tr><th>Échéance</th><th>Date</th><th>Commentaire</th></tr>
    {% if timeline.submission_deadline %}
    <tr class="risk-high"><td><strong>Date limite de remise</strong></td><td><span class="badge badge-red">{{ timeline.submission_deadline|datefr }}</span></td><td>Heure limite absolue</td></tr>
    {% endif %}
    {% if timeline.questions_deadline %}
    <tr><td>Date limite questions</td><td>{{ timeline.questions_deadline|datefr }}</td><td>Dernier jour pour poser des questions</td></tr>
    {% endif %}
    {% if timeline.site_visit_date %}
    <tr><td>Visite de site</td><td>{{ timeline.site_visit_date|datefr }}</td><td>{% if summary and summary.project_overview.site_visit_required %}Obligatoire{% else %}Facultative{% endif %}</td></tr>
    {% endif %}
    {% if timeline.execution_start %}
    <tr><td>Début d'exécution prévisionnel</td><td>{{ timeline.execution_start|datefr }}</td><td></td></tr>
    {% endif %}
    {% if timeline.execution_duration_months %}
    <tr><td>Durée d'exécution</td><td>{{ timeline.execution_duration_months }} mois</td><td></td></tr>
    {% endif %}
    {% for kd in timeline.key_dates %}
    <tr><td>{{ kd.label }}</td><td>{{ kd.date|datefr }}</td><td>{% if kd.mandatory %}<span class="badge badge-red">Obligatoire</span>{% endif %}</td></tr>
    {% endfor %}
  </table>
</div>
{% endif %}

<!-- ═══════════ CHECKLIST ═══════════ -->
{% if checklist_items %}
<div class="page page-break">
  <h1>5. Checklist de conformité ({{ checklist_items|length }} exigences)</h1>

  <div class="info-box">
    <strong>Note :</strong> Le statut "MANQUANT" indique les documents/justificatifs à préparer pour la soumission.
    Utilisez cette checklist comme liste de contrôle avant le dépôt de votre offre.
  </div>

  <!-- Statistiques checklist -->
  <div class="stat-grid">
    <div class="stat-cell" style="border-left: 3px solid #DC2626;">
      <div class="stat-number" style="color: #DC2626;">{{ checklist_stats.eliminatoire }}</div>
      <div class="stat-label">Éliminatoires</div>
    </div>
    <div class="stat-cell" style="border-left: 3px solid #D97706;">
      <div class="stat-number" style="color: #D97706;">{{ checklist_stats.important }}</div>
      <div class="stat-label">Importants</div>
    </div>
    <div class="stat-cell" style="border-left: 3px solid #64748B;">
      <div class="stat-number" style="color: #64748B;">{{ checklist_stats.info }}</div>
      <div class="stat-label">Informatifs</div>
    </div>
    <div class="stat-cell" style="border-left: 3px solid #16A34A;">
      <div class="stat-number" style="color: #16A34A;">{{ checklist_stats.ok }}</div>
      <div class="stat-label">Conformes</div>
    </div>
  </div>

  <table>
    <tr><th style="width:3%">#</th><th style="width:35%">Exigence</th><th style="width:12%">Catégorie</th><th style="width:12%">Criticité</th><th style="width:10%">Statut</th><th style="width:28%">À fournir</th></tr>
    {% for item in checklist_items %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ item.requirement }}
        {% for c in (item.citations or []) %}<div class="citation">{{ c.doc }} p.{{ c.page }}</div>{% endfor %}
      </td>
      <td>{{ item.category or '-' }}</td>
      <td><span class="badge {% if item.criticality == 'Éliminatoire' %}badge-red{% elif item.criticality == 'Important' %}badge-yellow{% else %}badge-gray{% endif %}">{{ item.criticality or '-' }}</span></td>
      <td><span class="badge {% if item.status == 'OK' %}badge-green{% elif item.status == 'MANQUANT' %}badge-red{% else %}badge-yellow{% endif %}">{{ item.status }}</span></td>
      <td style="font-size: 8px;">{{ item.what_to_provide or '-' }}</td>
    </tr>
    {% endfor %}
  </table>

  <!-- Documents prioritaires à préparer (éliminatoires MANQUANTS) -->
  {% set elim_manquants = [] %}
  {% for item in checklist_items %}
    {% if item.criticality and 'liminatoire' in item.criticality|lower and item.status == 'MANQUANT' %}
      {% if elim_manquants.append(item) %}{% endif %}
    {% endif %}
  {% endfor %}
  {% if elim_manquants %}
  <div class="page-break"></div>
  <h2 style="color: #DC2626;">Documents prioritaires à préparer ({{ elim_manquants|length }} éliminatoires)</h2>
  <div class="warning-box">
    <strong>Attention :</strong> Ces {{ elim_manquants|length }} documents sont <strong>éliminatoires</strong>.
    Leur absence entraînera le rejet automatique de votre candidature. Préparez-les en priorité absolue.
  </div>
  <table>
    <tr><th style="width:5%">#</th><th style="width:50%">Document / Justificatif requis</th><th style="width:45%">Détail à fournir</th></tr>
    {% for item in elim_manquants %}
    <tr class="risk-high">
      <td>{{ loop.index }}</td>
      <td><strong>{{ item.requirement }}</strong></td>
      <td style="font-size: 8px;">{{ item.what_to_provide or 'Voir exigences du RC/CCAP' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
</div>
{% endif %}

<!-- ═══════════ CRITÈRES D'ATTRIBUTION ═══════════ -->
{% if criteria %}
<div class="page page-break">
  <h1>6. Critères d'attribution</h1>

  {% if criteria.evaluation.eligibility_conditions %}
  <h3>Conditions d'éligibilité ({{ criteria.evaluation.eligibility_conditions|length }})</h3>
  <table>
    <tr><th style="width:80%">Condition</th><th style="width:20%">Type</th></tr>
    {% for c in criteria.evaluation.eligibility_conditions %}
    <tr>
      <td>{{ c.condition }}</td>
      <td><span class="badge {% if c.type == 'hard' %}badge-red{% else %}badge-yellow{% endif %}">{{ c.type|upper }}</span></td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  {% if criteria.evaluation.scoring_criteria %}
  <h3>Grille de notation</h3>
  <table>
    <tr><th style="width:40%">Critère</th><th style="width:15%">Pondération</th><th style="width:45%">Notes et recommandations</th></tr>
    {% for c in criteria.evaluation.scoring_criteria %}
    <tr>
      <td><strong>{{ c.criterion }}</strong></td>
      <td><span class="badge badge-blue">{% if c.weight_percent %}{{ c.weight_percent }}%{% else %}N/S{% endif %}</span></td>
      <td>{{ c.notes or '-' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
</div>
{% endif %}

<!-- ═══════════ SIMULATION NOTE ACHETEUR ═══════════ -->
{% if scoring_simulation %}
<div class="page page-break">
  <h1>6b. Simulation de la note acheteur</h1>
  <p style="color: #64748B; font-size: 9px;">Estimation de votre note finale basée sur les critères de notation du DCE et votre profil entreprise</p>

  <div class="gonogo-box" style="background: #EFF6FF; border: 2px solid #1E40AF;">
    <div class="gonogo-score" style="color: #1E40AF;">{{ "%.1f"|format(scoring_simulation.total_score) }}/20</div>
    <div class="gonogo-label" style="color: #1E40AF;">Note estimée</div>
    {% if scoring_simulation.rank_estimate %}
    <div style="font-size: 10px; margin-top: 4px; color: #64748B;">Position estimée : {{ scoring_simulation.rank_estimate }}</div>
    {% endif %}
  </div>

  {% if scoring_simulation.criteria_scores %}
  <h3>Détail par critère</h3>
  <table>
    <tr><th style="width:35%">Critère</th><th style="width:15%">Pondération</th><th style="width:15%">Note estimée</th><th style="width:35%">Recommandation</th></tr>
    {% for cs in scoring_simulation.criteria_scores %}
    <tr>
      <td><strong>{{ cs.criterion }}</strong></td>
      <td>{{ cs.weight }}%</td>
      <td><span class="badge {% if cs.score >= 14 %}badge-green{% elif cs.score >= 10 %}badge-yellow{% else %}badge-red{% endif %}">{{ "%.1f"|format(cs.score) }}/20</span></td>
      <td style="font-size: 8px;">{{ cs.recommendation or '-' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  {% if scoring_simulation.improvement_levers %}
  <h3>Leviers d'amélioration (gain potentiel)</h3>
  <table>
    <tr><th style="width:40%">Action</th><th style="width:15%">Gain estimé</th><th style="width:45%">Détail</th></tr>
    {% for lever in scoring_simulation.improvement_levers[:5] %}
    <tr>
      <td><strong>{{ lever.action }}</strong></td>
      <td><span class="badge badge-green">+{{ "%.1f"|format(lever.gain) }} pts</span></td>
      <td style="font-size: 8px;">{{ lever.detail or '' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  <div class="info-box">
    <strong>Note :</strong> Cette simulation est indicative. La note réelle dépend de la qualité de votre offre technique,
    du nombre de concurrents et de l'appréciation subjective de la commission d'attribution.
  </div>
</div>
{% endif %}

<!-- ═══════════ DÉROGATIONS CCAG ═══════════ -->
{% if ccag_derogations %}
<div class="page page-break">
  <h1>6c. Dérogations au CCAG-Travaux 2021</h1>
  <p style="color: #64748B; font-size: 9px;">Clauses du CCAP/CCTP qui dérogent au CCAG-Travaux 2021 — à vérifier pour le chiffrage</p>

  <div class="warning-box">
    <strong>Attention :</strong> {{ ccag_derogations|length }} dérogation{{ 's' if ccag_derogations|length > 1 else '' }}
    au CCAG-Travaux 2021 détectée{{ 's' if ccag_derogations|length > 1 else '' }}.
    Certaines peuvent avoir un impact significatif sur votre prix et vos risques contractuels.
  </div>

  <table>
    <tr><th style="width:15%">Article CCAG</th><th style="width:30%">Clause standard</th><th style="width:30%">Dérogation CCAP</th><th style="width:10%">Impact</th><th style="width:15%">Risque</th></tr>
    {% for d in ccag_derogations %}
    <tr>
      <td><strong>Art. {{ d.article }}</strong></td>
      <td style="font-size: 8px;">{{ d.standard_clause }}</td>
      <td style="font-size: 8px;">{{ d.derogation }}</td>
      <td><span class="badge {% if d.impact == 'fort' %}badge-red{% elif d.impact == 'moyen' %}badge-yellow{% else %}badge-gray{% endif %}">{{ d.impact|upper }}</span></td>
      <td style="font-size: 8px;">{{ d.risk_comment or '' }}</td>
    </tr>
    {% endfor %}
  </table>

  <div class="info-box">
    <strong>Conseil :</strong> Intégrez ces dérogations dans votre chiffrage. En particulier, vérifiez les pénalités
    (art. 20), les délais de paiement (art. 11), la retenue de garantie (art. 32) et les conditions de résiliation (art. 46).
  </div>
</div>
{% endif %}

<!-- ═══════════ FICHE SIGNALÉTIQUE DU MARCHÉ ═══════════ -->
{% if rc_analysis %}
<div class="page page-break">
  <h1>2b. Fiche signalétique du marché</h1>
  <p style="color: #64748B; font-size: 9px;">Données extraites du Règlement de Consultation (RC) et des pièces contractuelles</p>

  <table>
    <tr><th style="width:35%">Élément</th><th style="width:65%">Valeur</th></tr>
    {% if rc_analysis.procedure_type %}
    <tr><td><strong>Procédure</strong></td><td>{{ rc_analysis.procedure_type }}</td></tr>
    {% endif %}
    {% if rc_analysis.allotissement %}
    <tr><td><strong>Allotissement</strong></td><td>{{ rc_analysis.allotissement }}</td></tr>
    {% endif %}
    {% if rc_analysis.groupement %}
    <tr><td><strong>Groupement</strong></td><td>{{ rc_analysis.groupement }}</td></tr>
    {% endif %}
    {% if rc_analysis.variantes %}
    <tr><td><strong>Variantes</strong></td><td>{{ rc_analysis.variantes }}</td></tr>
    {% endif %}
    {% if rc_analysis.subcontracting_allowed is not none %}
    <tr><td><strong>Sous-traitance</strong></td><td>{% if rc_analysis.subcontracting_allowed %}Autorisée{% else %}Non autorisée{% endif %}</td></tr>
    {% endif %}
    {% if rc_analysis.ccag_reference %}
    <tr><td><strong>CCAG de référence</strong></td><td>{{ rc_analysis.ccag_reference }}</td></tr>
    {% endif %}
    {% if rc_analysis.visite_obligatoire is not none %}
    <tr><td><strong>Visite de site</strong></td><td>{% if rc_analysis.visite_obligatoire %}<span class="badge badge-red">OBLIGATOIRE</span>{% else %}Facultative{% endif %}</td></tr>
    {% endif %}
    {% if rc_analysis.dume_required is not none %}
    <tr><td><strong>DUME</strong></td><td>{% if rc_analysis.dume_required %}Requis{% else %}Non requis{% endif %}</td></tr>
    {% endif %}
  </table>

  {% if rc_analysis.lots %}
  <h3>Décomposition en lots</h3>
  <table>
    <tr><th style="width:10%">N°</th><th style="width:50%">Intitulé</th><th style="width:40%">Montant estimé</th></tr>
    {% for lot in rc_analysis.lots %}
    <tr>
      <td>{{ lot.number }}</td>
      <td>{{ lot.title }}</td>
      <td>{{ lot.estimated_amount or 'Non précisé' }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
</div>
{% endif %}

<!-- ═══════════ QUESTIONS POUR L'ACHETEUR ═══════════ -->
{% if questions_list %}
<div class="page page-break">
  <h1>8. Questions prioritaires pour l'acheteur</h1>
  <p style="color: #64748B; font-size: 9px;">Questions à poser à l'acheteur avant la date limite — classées par priorité</p>

  <div class="info-box">
    <strong>Conseil :</strong> Posez ces questions via la plateforme de dématérialisation
    avant la date limite de questions. Les réponses seront diffusées à tous les candidats.
  </div>

  <table>
    <tr><th style="width:5%">#</th><th style="width:10%">Priorité</th><th style="width:55%">Question</th><th style="width:30%">Justification</th></tr>
    {% for q in questions_list[:15] %}
    <tr>
      <td>{{ loop.index }}</td>
      <td><span class="badge {% if q.priority == 'high' %}badge-red{% elif q.priority == 'medium' %}badge-yellow{% else %}badge-gray{% endif %}">{{ q.priority|upper if q.priority else 'INFO' }}</span></td>
      <td>{{ q.question }}</td>
      <td style="font-size: 8px;">{{ q.justification or '' }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

<!-- ═══════════ INVENTAIRE DOCUMENTS ANALYSÉS ═══════════ -->
{% if documents_inventory %}
<div class="page page-break">
  <h1>A1. Inventaire des documents analysés</h1>
  <p style="color: #64748B; font-size: 9px;">Liste des pièces du DCE prises en compte dans cette analyse</p>

  <table>
    <tr><th style="width:5%">#</th><th style="width:40%">Document</th><th style="width:15%">Type</th><th style="width:10%">Pages</th><th style="width:15%">Taille</th><th style="width:15%">Qualité OCR</th></tr>
    {% for doc in documents_inventory %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ doc.name }}</td>
      <td><span class="badge badge-blue">{{ doc.doc_type or 'AUTRES' }}</span></td>
      <td>{{ doc.pages or '—' }}</td>
      <td>{{ doc.size_display }}</td>
      <td>
        {% if doc.ocr_quality %}
        <span class="badge {% if doc.ocr_quality >= 70 %}badge-green{% elif doc.ocr_quality >= 40 %}badge-yellow{% else %}badge-red{% endif %}">{{ "%.0f"|format(doc.ocr_quality) }}%</span>
        {% else %}—{% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>

  <div style="margin-top: 8px; font-size: 9px; color: #64748B;">
    Total : {{ documents_inventory|length }} document{{ 's' if documents_inventory|length > 1 else '' }}
    {% set total_pages = documents_inventory|sum(attribute='pages') %}
    {% if total_pages %} — {{ total_pages }} pages analysées{% endif %}
  </div>
</div>
{% endif %}

<!-- ═══════════ SYNTHÈSE FINANCIÈRE ═══════════ -->
{% if summary %}
<div class="page page-break">
  <h1>7. Synthèse financière</h1>
  <p style="color: #64748B; font-size: 9px;">Éléments financiers clés extraits du DCE pour l'aide à la décision</p>

  <div class="financial-box">
    <strong>Budget global estimé :</strong> {{ summary.project_overview.estimated_budget or 'Non précisé dans le DCE' }}<br>
    <strong>Type de prix :</strong> {{ summary.project_overview.market_type or 'Non précisé' }}
  </div>

  <!-- Extraction des données financières depuis key_points -->
  <h3>Éléments financiers extraits</h3>
  <table>
    <tr><th style="width:40%">Élément</th><th style="width:60%">Détail</th></tr>
    {% for kp in summary.key_points %}
    {% if 'prix' in kp.label|lower or 'avance' in kp.label|lower or 'retenue' in kp.label|lower or 'paiement' in kp.label|lower or 'pénalité' in kp.label|lower or 'révision' in kp.label|lower or 'financ' in kp.label|lower or 'budget' in kp.label|lower or 'garantie' in kp.label|lower %}
    <tr>
      <td><strong>{{ kp.label }}</strong></td>
      <td>{{ kp.value }}</td>
    </tr>
    {% endif %}
    {% endfor %}
  </table>

  {% if summary.risks %}
  <h3>Risques financiers identifiés</h3>
  <table>
    <tr><th style="width:40%">Risque</th><th style="width:10%">Sévérité</th><th style="width:50%">Impact financier</th></tr>
    {% for r in summary.risks %}
    {% if 'financ' in r.why|lower or 'prix' in r.risk|lower or 'pénalité' in r.risk|lower or 'coût' in r.why|lower or 'trésorerie' in r.why|lower or 'paiement' in r.risk|lower %}
    <tr class="risk-{{ r.severity }}">
      <td><strong>{{ r.risk }}</strong></td>
      <td><span class="badge {% if r.severity == 'high' %}badge-red{% elif r.severity == 'medium' %}badge-yellow{% else %}badge-gray{% endif %}">{{ r.severity|upper }}</span></td>
      <td>{{ r.why }}</td>
    </tr>
    {% endif %}
    {% endfor %}
  </table>
  {% endif %}

  <div class="warning-box">
    <strong>Recommandation :</strong> Avant de chiffrer votre offre, vérifiez les éléments suivants :
    formule de révision des prix, montant de l'avance, conditions de paiement, pénalités de retard,
    retenue de garantie, et tout risque de surcoût identifié (pollution, aléas géotechniques, etc.).
  </div>
</div>
{% endif %}

<!-- ═══════════ FOOTER & DISCLAIMER ═══════════ -->
<div class="page page-break">
  <div class="disclaimer">
    <strong>Avertissement IA :</strong> Ce rapport est généré par intelligence artificielle (Claude, Anthropic) à partir des documents du DCE fournis.
    Il constitue une aide à la décision et ne se substitue pas à l'analyse humaine d'un expert marchés publics.
    Les informations doivent être vérifiées avant toute soumission d'offre.
    Confiance globale de l'analyse : {{ "%.0f"|format(confidence * 100) if confidence else 'N/A' }}%.
  </div>
  <div class="footer">
    Généré par AO Copilot — aocopilot.fr — {{ generated_at }} — Rapport confidentiel
  </div>
</div>

</body>
</html>
"""


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
        """Allow dict.key access in Jinja2 templates."""
        def __init__(self, d):
            for k, v in (d or {}).items():
                if isinstance(v, list):
                    setattr(self, k, [_DictObj(i) if isinstance(i, dict) else i for i in v])
                elif isinstance(v, dict):
                    setattr(self, k, _DictObj(v))
                else:
                    setattr(self, k, v)
        def __bool__(self):
            return True
        def __getattr__(self, name):
            return None  # Return None for missing attributes instead of raising

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

    # ── Extract CCAG derogations from CCAP analysis (if available) ──
    ccap_result = db.query(ExtractionResult).filter_by(
        project_id=pid, result_type="ccap"
    ).order_by(ExtractionResult.version.desc()).first()
    ccag_derogations = None
    if ccap_result and ccap_result.payload:
        ccag_derogations = ccap_result.payload.get("ccag_derogations") or ccap_result.payload.get("derogations")

    # ── Extract RC analysis for fiche signalétique (if available) ──
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

    template = env.from_string(EXPORT_TEMPLATE)

    try:
        html_content = template.render(
            project=project,
            summary=summary_result.payload if summary_result else None,
            checklist_items=checklist_items,
            criteria=criteria_result.payload if criteria_result else None,
            gonogo=gonogo_obj,
            timeline=timeline_obj,
            checklist_stats=checklist_stats,
            confidence=confidence,
            days_remaining=days_remaining,
            scoring_simulation=_DictObj(scoring_simulation) if scoring_simulation else None,
            ccag_derogations=[_DictObj(d) for d in ccag_derogations] if ccag_derogations else None,
            rc_analysis=_DictObj(rc_analysis) if rc_analysis else None,
            questions_list=[_DictObj(q) if isinstance(q, dict) else q for q in questions_list] if questions_list else None,
            documents_inventory=[_DictObj(d) for d in documents_inventory] if documents_inventory else None,
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
