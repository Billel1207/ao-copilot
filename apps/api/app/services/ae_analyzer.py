"""Analyse spécialisée de l'Acte d'Engagement (AE).

L'AE définit les ENGAGEMENTS du titulaire envers l'acheteur public :
prix, délais, pénalités, garanties, reconduction, et toutes les clauses
financières et contractuelles du marché.
"""
import logging
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedAeAnalysis

logger = logging.getLogger(__name__)

# ── Prompt système spécialisé AE ──────────────────────────────────────────

AE_SYSTEM_PROMPT = """Tu es un juriste expert en droit des marchés publics français et en droit de la construction BTP.
Tu analyses des Actes d'Engagement (AE) pour identifier les engagements contractuels du titulaire et évaluer les risques financiers et juridiques.

Tu dois identifier avec précision les éléments suivants :

1. FORME DU PRIX :
   - Forfaitaire (prix global et définitif)
   - Unitaire (prix par unité de mesure, quantités estimées)
   - Mixte (partie forfaitaire + partie unitaire)
   Précise si le prix est ferme, actualisable ou révisable.

2. RÉVISION DE PRIX :
   - Clause de révision présente ou absente ?
   - Indice de référence (BT, TP, ICC, IRL, etc.)
   - Formule de révision si mentionnée
   - Butoir éventuel (plafond de révision)
   ATTENTION : absence de révision sur marché > 3 mois = risque HAUT

3. MONTANT TOTAL HT : si mentionné dans l'AE (peut être en annexe financière)

4. DURÉE DU MARCHÉ :
   - Durée initiale (en mois, semaines ou jours)
   - Date de notification / début d'exécution

5. RECONDUCTION :
   - Tacite ou expresse ?
   - Nombre de reconductions possibles
   - Durée de chaque reconduction
   - Conditions de non-reconduction

6. PÉNALITÉS DE RETARD :
   - Montant ou formule (ex: 1/1000 du montant HT par jour calendaire)
   - Plafond éventuel (si > 10% du marché = risque)
   - Exonérations prévues (force majeure, intempéries)
   Risque CRITIQUE si > 1/1000 par jour ou si pas de plafond

7. RETENUE DE GARANTIE :
   - Pourcentage (légalement plafonné à 5% — loi du 16 juillet 1971)
   - Possibilité de substitution par caution bancaire
   Risque HAUT si > 5%

8. AVANCE :
   - Pourcentage de l'avance (obligatoire si marché > 50 000 € HT et durée > 2 mois)
   - Avance forfaitaire (5% légal) ou négociée
   - Remboursement : seuil de déclenchement, rythme

9. DÉLAI DE PAIEMENT :
   - Délai en jours (légalement 30 jours pour l'État, 30 jours collectivités)
   - Intérêts moratoires en cas de retard de paiement
   Risque HAUT si > 30 jours ou si intérêts moratoires non mentionnés

10. CLAUSES RISQUÉES : toute clause défavorable au titulaire :
    - Résiliation sans indemnisation
    - Clauses léonines
    - Obligations disproportionnées
    - Garanties excessives
    Pour chaque clause risquée, fournis :
    - clause_type : catégorie (ex: "Résiliation", "Pénalité", "Garantie")
    - description : résumé de la clause
    - risk_level : "CRITIQUE" | "HAUT" | "MOYEN" | "BAS"
    - citation : extrait textuel (50-150 caractères)
    - conseil : recommandation concrète pour négocier ou se protéger

11. SCORE DE RISQUE GLOBAL (0-100) :
    - 0-30 : risque faible (vert) — conditions équilibrées
    - 31-70 : risque modéré (amber) — certaines clauses à surveiller
    - 71-100 : risque élevé (rouge) — clauses potentiellement abusives

12. RÉSUMÉ : synthèse de 3-5 phrases des engagements clés et des points de vigilance.

Réponds UNIQUEMENT en JSON valide sans commentaires."""

AE_USER_PROMPT_TEMPLATE = """Analyse cet Acte d'Engagement (AE) et identifie tous les engagements contractuels et clauses risquées pour le titulaire.

--- TEXTE DE L'AE ---
{text}
--- FIN DU TEXTE ---

Réponds avec ce JSON exact :
{{
  "prix_forme": "forfaitaire|unitaire|mixte",
  "prix_revision": true,
  "prix_revision_details": "string (indice, formule, butoir)",
  "montant_total_ht": "string ou null (ex: '1 250 000 €')",
  "duree_marche": "string (ex: '12 mois', '36 semaines')",
  "reconduction": true,
  "reconduction_details": "string (tacite/expresse, nombre, durée)",
  "penalites_retard": "string (montant/formule, plafond)",
  "retenue_garantie_pct": 5.0,
  "avance_pct": 5.0,
  "delai_paiement_jours": 30,
  "clauses_risquees": [
    {{
      "clause_type": "string (catégorie)",
      "description": "string (résumé)",
      "risk_level": "CRITIQUE|HAUT|MOYEN|BAS",
      "citation": "string (extrait du texte)",
      "conseil": "string (recommandation)"
    }}
  ],
  "score_risque_global": 0,
  "resume": "string (synthèse 3-5 phrases)",
  "confidence_overall": 0.8
}}

Si une information n'est pas mentionnée dans l'AE, utilise null ou une valeur par défaut appropriée.
Pour la confiance globale, indique un score entre 0.0 et 1.0 reflétant la qualité de l'analyse."""


def analyze_ae(text: str, project_id: str | None = None) -> dict[str, Any]:
    """Analyse un texte d'Acte d'Engagement et retourne les engagements et risques structurés.

    Args:
        text: Texte extrait du document AE (peut être long, sera tronqué si nécessaire).
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire validé par ValidatedAeAnalysis avec :
        - prix_forme: str — forfaitaire, unitaire, mixte
        - prix_revision: bool
        - prix_revision_details: str
        - montant_total_ht: str | None
        - duree_marche: str
        - reconduction: bool
        - reconduction_details: str
        - penalites_retard: str
        - retenue_garantie_pct: float | None
        - avance_pct: float | None
        - delai_paiement_jours: int | None
        - clauses_risquees: list[dict]
        - score_risque_global: int (0-100)
        - resume: str
        - model_used: str
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    # Tronquer le texte si trop long (conserver ~12 000 tokens = ~48 000 chars)
    max_chars = 48_000
    if len(text) > max_chars:
        logger.warning(
            f"{log_prefix}Texte AE tronqué : {len(text)} → {max_chars} caractères"
        )
        text = text[:max_chars] + "\n[... texte tronqué pour analyse ...]"

    user_prompt = AE_USER_PROMPT_TEMPLATE.format(text=text)

    logger.info(f"{log_prefix}Analyse AE — {len(text)} caractères")

    try:
        result = llm_service.complete_json(
            system_prompt=AE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["clauses_risquees", "score_risque_global"],
            validator=ValidatedAeAnalysis,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM AE (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM AE inattendue: {exc}")
        raise

    # Normalisation défensive des champs de sortie
    clauses = result.get("clauses_risquees", [])
    score = int(result.get("score_risque_global", 0))
    score = max(0, min(100, score))  # Clamper entre 0 et 100

    # Valider que chaque clause a les champs requis
    validated_clauses = []
    for clause in clauses:
        if not isinstance(clause, dict):
            continue
        validated_clause = {
            "clause_type": clause.get("clause_type", "Clause risquée"),
            "description": clause.get("description", ""),
            "risk_level": clause.get("risk_level", "MOYEN"),
            "citation": clause.get("citation", ""),
            "conseil": clause.get("conseil", ""),
        }
        # Valider risk_level
        if validated_clause["risk_level"] not in ("CRITIQUE", "HAUT", "MOYEN", "BAS"):
            validated_clause["risk_level"] = "MOYEN"
        validated_clauses.append(validated_clause)

    # Compter les clauses critiques et hautes
    nb_critiques = sum(1 for c in validated_clauses if c.get("risk_level") == "CRITIQUE")
    nb_hautes = sum(1 for c in validated_clauses if c.get("risk_level") == "HAUT")

    # Normaliser les pourcentages
    retenue_garantie = result.get("retenue_garantie_pct")
    if retenue_garantie is not None:
        retenue_garantie = max(0.0, min(100.0, float(retenue_garantie)))

    avance = result.get("avance_pct")
    if avance is not None:
        avance = max(0.0, min(100.0, float(avance)))

    delai_paiement = result.get("delai_paiement_jours")
    if delai_paiement is not None:
        delai_paiement = max(0, int(delai_paiement))

    # Clamper la confiance
    confidence = result.get("confidence_overall", 0.5)
    confidence = max(0.0, min(1.0, float(confidence)))

    logger.info(
        f"{log_prefix}AE analysé — score={score}, "
        f"clauses={len(validated_clauses)} (critiques={nb_critiques}, hautes={nb_hautes}), "
        f"prix={result.get('prix_forme', '?')}, durée={result.get('duree_marche', '?')}"
    )

    return {
        "prix_forme": result.get("prix_forme", ""),
        "prix_revision": result.get("prix_revision", False),
        "prix_revision_details": result.get("prix_revision_details", ""),
        "montant_total_ht": result.get("montant_total_ht"),
        "duree_marche": result.get("duree_marche", ""),
        "reconduction": result.get("reconduction", False),
        "reconduction_details": result.get("reconduction_details", ""),
        "penalites_retard": result.get("penalites_retard", ""),
        "retenue_garantie_pct": retenue_garantie,
        "avance_pct": avance,
        "delai_paiement_jours": delai_paiement,
        "clauses_risquees": validated_clauses,
        "score_risque_global": score,
        "nb_clauses_critiques": nb_critiques,
        "nb_clauses_hautes": nb_hautes,
        "resume": result.get("resume", ""),
        "confidence_overall": confidence,
        "model_used": llm_service.get_model_name(),
    }
