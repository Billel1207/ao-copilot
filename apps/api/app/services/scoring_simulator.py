"""Simulation de la note que l'acheteur donnerait à l'offre.

Prend en entrée les critères d'attribution détectés (criteria_payload) et
le profil entreprise, puis simule note technique, note financière, note
globale, avec justifications et axes d'amélioration concrets.
"""
import logging
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedScoringSimulation

logger = logging.getLogger(__name__)

# ── Prompt système spécialisé Scoring ────────────────────────────────────────

SCORING_SYSTEM_PROMPT = """Tu es un expert en évaluation des offres dans les marchés publics français (Code de la commande publique).
Tu maîtrises parfaitement les méthodes de notation utilisées par les acheteurs publics :
- Méthode du rapport qualité/prix (pondération technique + prix)
- Notation sur 20 ou sur 100 par critère et sous-critère
- Barème proportionnel au moins-disant pour le prix
- Notation multicritère technique (valeur technique, mémoire technique, références, moyens, délais)

TON RÔLE :
Simuler la note que l'acheteur donnerait à l'offre d'une entreprise, en se basant sur :
1. Les critères d'attribution et leur pondération (extraits du RC/CCAP)
2. Le profil de l'entreprise candidate (si disponible)

POUR CHAQUE CRITÈRE, tu dois fournir :
- criterion : nom du critère tel que défini par l'acheteur
- weight_pct : pondération en % (telle que définie dans le DCE)
- estimated_score : note estimée (sur le barème max_score)
- max_score : barème maximum (20 par défaut, ou 100 si spécifié)
- justification : explication factuelle de la note estimée (2-3 phrases)
- tips_to_improve : liste de 1-3 actions concrètes pour améliorer la note sur ce critère

NOTES GLOBALES :
- note_technique_estimee : moyenne pondérée des critères techniques (sur 20)
- note_financiere_estimee : estimation de la note prix (sur 20), ou 0 si pas de donnée prix
- note_globale_estimee : note finale pondérée (sur 20)

CLASSEMENT PROBABLE :
- "Top 3" : offre bien positionnée, chances élevées d'attribution
- "Milieu de peloton" : offre correcte mais perfectible sur plusieurs points
- "Risqué" : offre qui présente des faiblesses notables, attribution peu probable

AXES D'AMÉLIORATION :
Liste de 3-5 recommandations concrètes et actionnables pour améliorer la position
concurrentielle de l'offre, classées par impact décroissant.

RÈGLES :
- Si le profil entreprise n'est pas fourni, simule un candidat "moyen" du secteur
- Sois réaliste et conservateur dans les estimations (mieux vaut sous-estimer)
- Base tes justifications sur les exigences spécifiques du DCE
- Ne surestime jamais : un critère sans preuve concrète = note médiane au mieux

Réponds UNIQUEMENT en JSON valide sans commentaires."""

SCORING_USER_PROMPT_TEMPLATE = """Simule la notation que l'acheteur donnerait à l'offre selon les critères d'attribution détectés dans le DCE.

--- CRITÈRES D'ATTRIBUTION ---
{criteria_section}
--- FIN DES CRITÈRES ---

{company_section}

Réponds avec ce JSON exact :
{{
  "dimensions": [
    {{
      "criterion": "Nom du critère",
      "weight_pct": 0.0,
      "estimated_score": 0.0,
      "max_score": 20,
      "justification": "Explication factuelle de la note estimée",
      "tips_to_improve": ["Action concrète 1", "Action concrète 2"]
    }}
  ],
  "note_technique_estimee": 0.0,
  "note_financiere_estimee": 0.0,
  "note_globale_estimee": 0.0,
  "classement_probable": "Top 3|Milieu de peloton|Risqué",
  "axes_amelioration": [
    "Recommandation concrète 1",
    "Recommandation concrète 2",
    "Recommandation concrète 3"
  ],
  "resume": "Synthèse en 2-3 phrases de l'évaluation simulée"
}}"""


def _format_criteria_section(criteria_payload: dict) -> str:
    """Formate le payload de critères en texte lisible pour le prompt."""
    lines: list[str] = []

    evaluation = criteria_payload.get("evaluation", criteria_payload)

    # Conditions d'éligibilité
    eligibility = evaluation.get("eligibility_conditions", [])
    if eligibility:
        lines.append("CONDITIONS D'ÉLIGIBILITÉ :")
        for ec in eligibility:
            cond = ec.get("condition", "") if isinstance(ec, dict) else str(ec)
            ctype = ec.get("type", "hard") if isinstance(ec, dict) else "hard"
            tag = "[ÉLIMINATOIRE]" if ctype == "hard" else "[RECOMMANDÉ]"
            lines.append(f"  {tag} {cond}")
        lines.append("")

    # Critères de notation
    scoring = evaluation.get("scoring_criteria", [])
    if scoring:
        lines.append("CRITÈRES DE NOTATION :")
        for sc in scoring:
            criterion = sc.get("criterion", "") if isinstance(sc, dict) else str(sc)
            weight = sc.get("weight_percent") if isinstance(sc, dict) else None
            notes = sc.get("notes", "") if isinstance(sc, dict) else ""
            weight_str = f" ({weight}%)" if weight is not None else ""
            lines.append(f"  - {criterion}{weight_str}")
            if notes:
                lines.append(f"    Note : {notes}")
        lines.append("")

    # Total pondération
    total = evaluation.get("total_weight_check")
    if total is not None:
        lines.append(f"Total pondérations vérifiées : {total}%")

    # Confiance
    confidence = evaluation.get("confidence")
    if confidence is not None:
        lines.append(f"Confiance extraction : {confidence}")

    if not lines:
        lines.append("Aucun critère d'attribution explicite détecté dans le DCE.")
        lines.append("Simule avec les critères standards :")
        lines.append("  - Valeur technique (60%)")
        lines.append("  - Prix des prestations (40%)")

    return "\n".join(lines)


def _format_company_section(company_profile: dict | None) -> str:
    """Formate le profil entreprise en texte lisible pour le prompt."""
    if not company_profile:
        return (
            "--- PROFIL ENTREPRISE ---\n"
            "Aucun profil entreprise fourni. Simule un candidat moyen du secteur BTP.\n"
            "--- FIN DU PROFIL ---"
        )

    lines = ["--- PROFIL ENTREPRISE ---"]

    mapping = [
        ("company_name", "Raison sociale"),
        ("revenue_eur", "Chiffre d'affaires (EUR)"),
        ("employee_count", "Effectif"),
        ("specialties", "Spécialités"),
        ("certifications", "Certifications"),
        ("regions", "Zones d'intervention"),
        ("max_market_size_eur", "Taille max marché (EUR)"),
        ("years_experience", "Années d'expérience"),
        ("references_count", "Nombre de références"),
    ]

    for key, label in mapping:
        value = company_profile.get(key)
        if value is not None and value != "" and value != []:
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"  {label} : {value}")

    # Références récentes si disponibles
    references = company_profile.get("recent_references", [])
    if references:
        lines.append("  Références récentes :")
        for ref in references[:5]:
            if isinstance(ref, dict):
                desc = ref.get("description", ref.get("title", ""))
                amount = ref.get("amount", "")
                year = ref.get("year", "")
                lines.append(f"    - {desc} ({amount} EUR, {year})")
            else:
                lines.append(f"    - {ref}")

    lines.append("--- FIN DU PROFIL ---")
    return "\n".join(lines)


def simulate_scoring(
    criteria_payload: dict,
    company_profile: dict | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Simule la note que l'acheteur donnerait à l'offre.

    Args:
        criteria_payload: Payload des critères d'attribution retourné par
            l'analyse LLM (ValidatedCriteria format, avec clé 'evaluation').
        company_profile: Données du profil entreprise (optionnel). Si None,
            simule un candidat moyen du secteur.
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire avec :
        - dimensions: list[dict] -- score par critère avec justification et tips
        - note_technique_estimee: float (sur 20)
        - note_financiere_estimee: float (sur 20)
        - note_globale_estimee: float (sur 20)
        - classement_probable: str ("Top 3" | "Milieu de peloton" | "Risqué")
        - axes_amelioration: list[str]
        - resume: str
        - model_used: str
        - has_company_profile: bool
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    criteria_section = _format_criteria_section(criteria_payload)
    company_section = _format_company_section(company_profile)

    user_prompt = SCORING_USER_PROMPT_TEMPLATE.format(
        criteria_section=criteria_section,
        company_section=company_section,
    )

    logger.info(
        f"{log_prefix}Simulation scoring acheteur — "
        f"profil={'oui' if company_profile else 'non'}"
    )

    try:
        result = llm_service.complete_json(
            system_prompt=SCORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["dimensions", "note_globale_estimee", "classement_probable"],
            validator=ValidatedScoringSimulation,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM scoring (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM scoring inattendue: {exc}")
        raise

    # Normalisation défensive
    dimensions = result.get("dimensions", [])
    note_technique = float(result.get("note_technique_estimee", 0))
    note_financiere = float(result.get("note_financiere_estimee", 0))
    note_globale = float(result.get("note_globale_estimee", 0))

    # Clamper les notes entre 0 et 20
    note_technique = max(0.0, min(20.0, note_technique))
    note_financiere = max(0.0, min(20.0, note_financiere))
    note_globale = max(0.0, min(20.0, note_globale))

    # Valider le classement
    classement = result.get("classement_probable", "Milieu de peloton")
    classements_valides = {"Top 3", "Milieu de peloton", "Risqué"}
    if classement not in classements_valides:
        # Best-effort mapping
        cl = classement.lower()
        if "top" in cl or "premier" in cl or "favori" in cl:
            classement = "Top 3"
        elif "risqu" in cl or "faible" in cl or "difficult" in cl:
            classement = "Risqué"
        else:
            classement = "Milieu de peloton"

    # Clamper les scores individuels des dimensions
    for dim in dimensions:
        max_score = float(dim.get("max_score", 20))
        estimated = float(dim.get("estimated_score", 0))
        dim["estimated_score"] = max(0.0, min(max_score, estimated))
        dim["max_score"] = max_score
        dim["weight_pct"] = max(0.0, min(100.0, float(dim.get("weight_pct", 0))))

    logger.info(
        f"{log_prefix}Scoring simulé — "
        f"technique={note_technique:.1f}/20, "
        f"financière={note_financiere:.1f}/20, "
        f"globale={note_globale:.1f}/20, "
        f"classement={classement}"
    )

    return {
        "dimensions": dimensions,
        "note_technique_estimee": round(note_technique, 1),
        "note_financiere_estimee": round(note_financiere, 1),
        "note_globale_estimee": round(note_globale, 1),
        "classement_probable": classement,
        "axes_amelioration": result.get("axes_amelioration", []),
        "resume": result.get("resume", ""),
        "model_used": llm_service.get_model_name(),
        "has_company_profile": company_profile is not None,
    }
