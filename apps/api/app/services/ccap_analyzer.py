"""Analyse spécialisée des clauses risquées dans les CCAP (Cahier des Clauses Administratives Particulières)."""
import logging
from typing import Any

from app.services.llm import llm_service

logger = logging.getLogger(__name__)

# ── Prompt système spécialisé CCAP ──────────────────────────────────────────

CCAP_SYSTEM_PROMPT = """Tu es un juriste expert en droit des marchés publics français et en droit de la construction BTP.
Tu analyses des CCAP (Cahiers des Clauses Administratives Particulières) pour identifier les clauses potentiellement risquées
pour l'entreprise titulaire du marché.

Tu dois repérer et évaluer les clauses suivantes selon la réglementation française (Code de la commande publique, loi MOP, etc.) :

1. PÉNALITÉS DE RETARD : risque CRITIQUE si > 1/1000 du montant du marché par jour calendaire
2. RETENUE DE GARANTIE : risque HAUT si > 5% du montant des travaux (seuil légal selon loi du 16 juillet 1971)
3. DÉLAIS D'EXÉCUTION TRÈS SERRÉS : risque HAUT si < 30 jours pour des prestations complexes
4. CLAUSES DE RÉSILIATION FACILITÉE : risque CRITIQUE si l'acheteur peut résilier sans motif légitime ou avec préavis très court
5. GARANTIES BANCAIRES EXORBITANTES : risque HAUT si cautions demandées dépassent les usages (>10% du marché)
6. CONDITIONS DE SOUS-TRAITANCE RESTRICTIVES : risque MOYEN à HAUT si contraires à la loi du 31 décembre 1975 relative à la sous-traitance
7. RÉVISION DE PRIX ABSENTE OU PLAFONNÉE : risque HAUT si durée > 3 mois sans clause de révision ou avec plafond < variation IRL/BTP
8. PAIEMENTS DIFFÉRÉS : risque HAUT si délai de paiement > 30 jours (hors délais légaux fixés par l'ordonnance 2019-359)

Pour chaque clause risquée détectée, fournis :
- article_reference : numéro ou titre de l'article concerné (ex: "Article 7.3", "Chapitre IV §2")
- clause_text : extrait textuel de la clause (100-200 caractères max)
- risk_level : "CRITIQUE" | "HAUT" | "MOYEN" | "BAS"
- risk_type : type de risque parmi les 8 catégories ci-dessus (en français court)
- conseil : recommandation concrète pour négocier ou se protéger (1-2 phrases)
- citation : passage exact de la clause (citation courte)

Le score_risque_global (0-100) reflète l'exposition globale :
- 0-30 : risque faible (vert)
- 31-70 : risque modéré (amber)
- 71-100 : risque élevé (rouge)

Réponds UNIQUEMENT en JSON valide sans commentaires."""

CCAP_USER_PROMPT_TEMPLATE = """Analyse ce CCAP et identifie toutes les clauses risquées pour l'entreprise titulaire.

--- TEXTE DU CCAP ---
{text}
--- FIN DU TEXTE ---

Réponds avec ce JSON exact :
{{
  "clauses_risquees": [
    {{
      "article_reference": "string",
      "clause_text": "string (extrait)",
      "risk_level": "CRITIQUE|HAUT|MOYEN|BAS",
      "risk_type": "string",
      "conseil": "string",
      "citation": "string"
    }}
  ],
  "score_risque_global": 0,
  "nb_clauses_critiques": 0,
  "resume_risques": "string (2-3 phrases résumant l'exposition)"
}}

Si aucune clause risquée n'est détectée, retourne une liste vide et score 0."""


def analyze_ccap_risks(text: str, project_id: str | None = None) -> dict[str, Any]:
    """Analyse un texte CCAP et retourne les clauses risquées détectées.

    Args:
        text: Texte extrait du document CCAP (peut être long, sera tronqué si nécessaire).
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire avec :
        - clauses_risquees: list[dict] — liste des clauses avec level, type, conseil, etc.
        - score_risque_global: int (0-100)
        - nb_clauses_critiques: int
        - resume_risques: str
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    # Tronquer le texte si trop long (conserver ~12 000 tokens = ~48 000 chars)
    max_chars = 48_000
    if len(text) > max_chars:
        logger.warning(
            f"{log_prefix}Texte CCAP tronqué : {len(text)} → {max_chars} caractères"
        )
        text = text[:max_chars] + "\n[... texte tronqué pour analyse ...]"

    user_prompt = CCAP_USER_PROMPT_TEMPLATE.format(text=text)

    logger.info(f"{log_prefix}Analyse CCAP — {len(text)} caractères")

    try:
        result = llm_service.complete_json(
            system_prompt=CCAP_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["clauses_risquees", "score_risque_global"],
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM CCAP (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM CCAP inattendue: {exc}")
        raise

    # Normalisation défensive des champs de sortie
    clauses = result.get("clauses_risquees", [])
    score = int(result.get("score_risque_global", 0))
    score = max(0, min(100, score))  # Clamper entre 0 et 100

    # Compter les critiques depuis la liste si le LLM ne l'a pas fourni
    nb_critiques_declared = result.get("nb_clauses_critiques")
    if nb_critiques_declared is None:
        nb_critiques = sum(1 for c in clauses if c.get("risk_level") == "CRITIQUE")
    else:
        nb_critiques = int(nb_critiques_declared)

    # Valider que chaque clause a les champs requis
    validated_clauses = []
    for clause in clauses:
        if not isinstance(clause, dict):
            continue
        validated_clause = {
            "article_reference": clause.get("article_reference", "—"),
            "clause_text": clause.get("clause_text", ""),
            "risk_level": clause.get("risk_level", "MOYEN"),
            "risk_type": clause.get("risk_type", "Clause risquée"),
            "conseil": clause.get("conseil", ""),
            "citation": clause.get("citation", ""),
        }
        # Valider risk_level
        if validated_clause["risk_level"] not in ("CRITIQUE", "HAUT", "MOYEN", "BAS"):
            validated_clause["risk_level"] = "MOYEN"
        validated_clauses.append(validated_clause)

    logger.info(
        f"{log_prefix}CCAP analysé — score={score}, "
        f"clauses={len(validated_clauses)}, critiques={nb_critiques}"
    )

    return {
        "clauses_risquees": validated_clauses,
        "score_risque_global": score,
        "nb_clauses_critiques": nb_critiques,
        "resume_risques": result.get("resume_risques", ""),
        "model_used": llm_service.get_model_name(),
    }
