"""Analyse spécialisée du Règlement de Consultation (RC).

Le RC définit QUI peut candidater et COMMENT répondre à l'appel d'offres.
Il fixe les conditions d'accès, les modalités de groupement, les critères
de sélection, et les règles de présentation des offres.
"""
import structlog
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedRcAnalysis

logger = structlog.get_logger(__name__)

# ── Prompt système spécialisé RC ──────────────────────────────────────────

RC_SYSTEM_PROMPT = """Tu es un expert en droit des marchés publics français, spécialisé dans l'analyse des Règlements de Consultation (RC).
Tu analyses les RC pour identifier toutes les conditions de candidature, les modalités de soumission et les contraintes procédurales.

Tu dois identifier avec précision les éléments suivants :

1. CONDITIONS D'ACCÈS : qui peut candidater ? Restrictions PME, artisans, entreprises étrangères ?
   Exigences de qualification, certification, agrément ? Chiffre d'affaires minimal ?
   Capacités techniques et professionnelles exigées ? Références similaires demandées ?

2. GROUPEMENT D'ENTREPRISES :
   - Le groupement est-il autorisé ?
   - Une forme est-elle imposée (solidaire ou conjoint) ?
   - Le mandataire doit-il être solidaire ?
   - Restrictions sur le nombre de membres ?

3. SOUS-TRAITANCE :
   - La sous-traitance est-elle autorisée ?
   - Y a-t-il des restrictions (pourcentage max, lots interdits, agrément préalable) ?
   - Présentation des sous-traitants au moment de l'offre ?

4. VARIANTES : autorisées ou non ? Si oui, conditions et encadrement ?

5. PRESTATIONS SUPPLÉMENTAIRES ÉVENTUELLES (PSE) : proposées ? Obligatoires ?

6. VISITE DE SITE : obligatoire ou facultative ? Date et modalités ?

7. LANGUE ET DEVISE des offres

8. DURÉE DE VALIDITÉ DES OFFRES (en jours)

9. TYPE DE PROCÉDURE : appel d'offres ouvert, restreint, procédure adaptée (MAPA),
   dialogue compétitif, procédure avec négociation, concours, etc.
   Référence au Code de la commande publique si mentionnée.

10. ALLOTISSEMENT : nombre de lots, description de chaque lot,
    possibilité de répondre à un ou plusieurs lots, limitations éventuelles.

11. RÉSUMÉ : synthèse de 3-5 phrases des points essentiels du RC.

Pour chaque condition d'accès, précise :
- condition : description claire de la condition
- type : "hard" (éliminatoire, obligatoire) ou "soft" (recommandé, non éliminatoire)
- details : précisions supplémentaires si pertinentes
- citations : référence au passage du document (doc, page, quote)

Réponds UNIQUEMENT en JSON valide sans commentaires."""

RC_USER_PROMPT_TEMPLATE = """Analyse ce Règlement de Consultation (RC) et identifie toutes les conditions de candidature, modalités de groupement, et règles de soumission.

--- TEXTE DU RC ---
{text}
--- FIN DU TEXTE ---

Réponds avec ce JSON exact :
{{
  "who_can_apply": [
    {{
      "condition": "string (description de la condition d'accès)",
      "type": "hard|soft",
      "details": "string (précisions)",
      "citations": [{{"doc": "string", "page": 0, "quote": "string"}}]
    }}
  ],
  "groupement": {{
    "groupement_autorise": true,
    "forme_imposee": "solidaire|conjoint|null (null si pas imposée)",
    "mandataire_solidaire": false,
    "details": "string"
  }},
  "sous_traitance": {{
    "sous_traitance_autorisee": true,
    "restrictions": ["string"],
    "details": "string"
  }},
  "variantes_autorisees": false,
  "variantes_details": "string",
  "prestations_supplementaires": false,
  "prestations_details": "string",
  "visite_site_obligatoire": false,
  "visite_details": "string (date, lieu, modalités si applicable)",
  "langue_offre": "français",
  "devise_offre": "EUR",
  "duree_validite_offres_jours": 120,
  "nombre_lots": 1,
  "lots_details": [
    {{
      "numero": 1,
      "intitule": "string",
      "description": "string",
      "montant_estime": "string ou null"
    }}
  ],
  "procedure_type": "string (type de procédure)",
  "resume": "string (synthèse 3-5 phrases)",
  "confidence_overall": 0.8
}}

Si une information n'est pas mentionnée dans le RC, utilise les valeurs par défaut.
Pour la confiance globale, indique un score entre 0.0 et 1.0 reflétant la qualité de l'analyse."""


def analyze_rc(text: str, project_id: str | None = None) -> dict[str, Any]:
    """Analyse un texte de Règlement de Consultation et retourne les conditions structurées.

    Args:
        text: Texte extrait du document RC (peut être long, sera tronqué si nécessaire).
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire validé par ValidatedRcAnalysis avec :
        - who_can_apply: list[dict] — conditions d'accès (condition, type, details, citations)
        - groupement: dict — règles de groupement
        - sous_traitance: dict — règles de sous-traitance
        - variantes_autorisees: bool
        - visite_site_obligatoire: bool
        - nombre_lots: int | None
        - lots_details: list[dict]
        - procedure_type: str
        - resume: str
        - model_used: str
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    # Tronquer le texte si trop long (conserver ~12 000 tokens = ~48 000 chars)
    max_chars = 48_000
    if len(text) > max_chars:
        logger.warning(
            f"{log_prefix}Texte RC tronqué : {len(text)} → {max_chars} caractères"
        )
        text = text[:max_chars] + "\n[... texte tronqué pour analyse ...]"

    user_prompt = RC_USER_PROMPT_TEMPLATE.format(text=text)

    logger.info(f"{log_prefix}Analyse RC — {len(text)} caractères")

    try:
        result = llm_service.complete_json(
            system_prompt=RC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["who_can_apply", "procedure_type"],
            validator=ValidatedRcAnalysis,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM RC (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM RC inattendue: {exc}")
        raise

    # Normalisation défensive des champs de sortie
    conditions = result.get("who_can_apply", [])
    groupement = result.get("groupement", {})
    sous_traitance = result.get("sous_traitance", {})
    lots = result.get("lots_details", [])
    nombre_lots = result.get("nombre_lots")

    # Valider chaque condition d'accès
    validated_conditions = []
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        validated_cond = {
            "condition": cond.get("condition", ""),
            "type": cond.get("type", "hard"),
            "details": cond.get("details", ""),
            "citations": cond.get("citations", []),
        }
        if validated_cond["type"] not in ("hard", "soft"):
            validated_cond["type"] = "hard"
        validated_conditions.append(validated_cond)

    # Valider les détails de lots
    validated_lots = []
    for lot in lots:
        if not isinstance(lot, dict):
            continue
        validated_lots.append({
            "numero": lot.get("numero", 0),
            "intitule": lot.get("intitule", ""),
            "description": lot.get("description", ""),
            "montant_estime": lot.get("montant_estime"),
        })

    # Réconcilier nombre_lots et lots_details
    if nombre_lots is None and validated_lots:
        nombre_lots = len(validated_lots)

    # Clamper la confiance
    confidence = result.get("confidence_overall", 0.5)
    confidence = max(0.0, min(1.0, float(confidence)))

    # Clamper la durée de validité
    duree_validite = result.get("duree_validite_offres_jours")
    if duree_validite is not None:
        duree_validite = max(1, int(duree_validite))

    nb_conditions_hard = sum(
        1 for c in validated_conditions if c.get("type") == "hard"
    )

    logger.info(
        f"{log_prefix}RC analysé — conditions={len(validated_conditions)} "
        f"(éliminatoires={nb_conditions_hard}), "
        f"lots={nombre_lots or 0}, procédure={result.get('procedure_type', '?')}"
    )

    return {
        "who_can_apply": validated_conditions,
        "groupement": {
            "groupement_autorise": groupement.get("groupement_autorise", True),
            "forme_imposee": groupement.get("forme_imposee"),
            "mandataire_solidaire": groupement.get("mandataire_solidaire", False),
            "details": groupement.get("details", ""),
        },
        "sous_traitance": {
            "sous_traitance_autorisee": sous_traitance.get("sous_traitance_autorisee", True),
            "restrictions": sous_traitance.get("restrictions", []),
            "details": sous_traitance.get("details", ""),
        },
        "variantes_autorisees": result.get("variantes_autorisees", False),
        "variantes_details": result.get("variantes_details", ""),
        "prestations_supplementaires": result.get("prestations_supplementaires", False),
        "prestations_details": result.get("prestations_details", ""),
        "visite_site_obligatoire": result.get("visite_site_obligatoire", False),
        "visite_details": result.get("visite_details", ""),
        "langue_offre": result.get("langue_offre", "français"),
        "devise_offre": result.get("devise_offre", "EUR"),
        "duree_validite_offres_jours": duree_validite,
        "nombre_lots": nombre_lots,
        "lots_details": validated_lots,
        "procedure_type": result.get("procedure_type", ""),
        "resume": result.get("resume", ""),
        "confidence_overall": confidence,
        "model_used": llm_service.get_model_name(),
    }
