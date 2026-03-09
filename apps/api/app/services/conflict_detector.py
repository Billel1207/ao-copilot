"""Détecteur de conflits et contradictions entre les pièces du DCE.

Compare les textes du RC, CCTP, CCAP (et autres documents) pour identifier :
- Contradictions de délais, quantités, montants
- Exigences contradictoires entre documents
- Clauses potentiellement illégales
- Incohérences de références croisées
"""
import logging
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedConflicts

logger = logging.getLogger(__name__)

# ── Prompt système expert juriste BTP ────────────────────────────────────────

CONFLICT_SYSTEM_PROMPT = """Tu es un juriste expert en droit des marchés publics français et en droit de la construction BTP.
Tu analyses plusieurs pièces d'un même DCE (Dossier de Consultation des Entreprises) pour détecter les CONTRADICTIONS et INCOHÉRENCES entre documents.

Dans un DCE, la hiérarchie des pièces contractuelles est généralement :
1. L'Acte d'Engagement (AE/ATTRI1)
2. Le CCAP (Cahier des Clauses Administratives Particulières)
3. Le CCTP (Cahier des Clauses Techniques Particulières)
4. Le RC (Règlement de Consultation)
5. Le BPU/DPGF (Bordereau des Prix Unitaires / Décomposition du Prix Global et Forfaitaire)

TYPES DE CONFLITS À DÉTECTER :

1. CONTRADICTIONS DE DÉLAIS :
   - Le RC annonce un délai d'exécution différent du CCAP ou CCTP
   - Délai de remise des offres incohérent entre RC et avis de publicité
   - Délai de paiement différent entre AE et CCAP
   - Période de garantie contradictoire entre CCAP et CCTP
   Exemple : RC dit "délai d'exécution : 30 jours", CCTP dit "durée des travaux : 45 jours ouvrés"

2. CONTRADICTIONS DE QUANTITÉS OU MONTANTS :
   - Quantités du DPGF/BPU ne correspondent pas aux descriptifs du CCTP
   - Montant estimé du marché différent entre RC et CCAP
   - Taux de pénalités différents entre CCAP et AE
   - Retenue de garantie : pourcentage contradictoire entre documents
   Exemple : DPGF mentionne "150 m² de peinture", CCTP décrit "200 m² de surfaces à peindre"

3. EXIGENCES CONTRADICTOIRES :
   - Le RC exige une certification non mentionnée dans le CCAP
   - Conditions de sous-traitance différentes entre RC et CCAP
   - Modalités de remise des offres contradictoires (papier vs électronique)
   - Variantes autorisées dans le RC mais interdites dans l'AE
   - Critères d'attribution différents entre RC et avis de publicité
   Exemple : RC autorise les variantes, AE les interdit

4. CLAUSES POTENTIELLEMENT ILLÉGALES :
   - Pénalités de retard > 1/1000 du montant par jour (disproportionné)
   - Retenue de garantie > 5% (seuil légal loi du 16 juillet 1971)
   - Délai de paiement > 30 jours sans justification (ordonnance 2019-359)
   - Garantie à première demande pour marché < 100 000 EUR
   - Clause de résiliation unilatérale sans indemnisation
   - Avance forfaitaire refusée pour marché > 50 000 EUR HT (article R2191-3 CCP)
   - Clause d'exclusivité de sous-traitance contraire à la loi du 31 décembre 1975
   - Clause pénale manifestement disproportionnée (article 1231-5 Code civil)

5. INCOHÉRENCES DE RÉFÉRENCES :
   - Article du CCTP renvoyant à un article du CCAP qui n'existe pas
   - Norme technique citée mais version obsolète ou retirée
   - Annexe mentionnée mais absente du DCE
   - Lot référencé dans un document mais non défini dans le RC
   Exemple : CCTP mentionne "conformément à l'article 14.3 du CCAP" mais le CCAP n'a que 12 articles

Pour CHAQUE conflit détecté, fournis :
- conflict_type : "delai" | "montant" | "exigence" | "clause_illegale" | "reference"
- severity : "CRITIQUE" | "HAUT" | "MOYEN" | "BAS"
  * CRITIQUE : contradiction bloquante pouvant invalider le marché ou causer un litige majeur
  * HAUT : incohérence significative nécessitant une clarification avant soumission
  * MOYEN : ambiguïté à signaler dans les questions à l'acheteur
  * BAS : divergence mineure, probablement une erreur de rédaction
- doc_a : document source A (ex: "RC", "CCAP")
- doc_b : document source B (ex: "CCTP", "DPGF")
- description : explication claire du conflit (2-3 phrases)
- citation_a : extrait du document A justifiant le conflit
- citation_b : extrait du document B montrant la contradiction
- recommendation : conseil actionnable (1-2 phrases) — ex: "Poser une question écrite à l'acheteur pour clarifier le délai applicable"

RÈGLES IMPORTANTES :
- Ne signale PAS les différences normales de formulation entre documents (reformulations acceptables)
- Concentre-toi sur les contradictions SUBSTANTIELLES (chiffres, dates, exigences factuelles)
- Si un document est plus récent ou hiérarchiquement supérieur, mentionne-le dans la recommendation
- Compte séparément les conflits CRITIQUES (nb_critiques) et le total (nb_total)

Réponds UNIQUEMENT en JSON valide sans commentaires ni texte autour."""

CONFLICT_USER_PROMPT_TEMPLATE = """Analyse ces pièces du même DCE et identifie TOUTES les contradictions et incohérences entre documents.

{documents_block}

Réponds avec ce JSON exact :
{{
  "conflicts": [
    {{
      "conflict_type": "delai|montant|exigence|clause_illegale|reference",
      "severity": "CRITIQUE|HAUT|MOYEN|BAS",
      "doc_a": "string (nom du document A)",
      "doc_b": "string (nom du document B)",
      "description": "string (explication du conflit)",
      "citation_a": "string (extrait du document A)",
      "citation_b": "string (extrait du document B)",
      "recommendation": "string (conseil actionnable)"
    }}
  ],
  "nb_critiques": 0,
  "nb_total": 0,
  "resume": "string (2-3 phrases résumant les conflits détectés et leur gravité)",
  "confidence_overall": 0.85
}}

Si aucun conflit n'est détecté, retourne une liste vide avec nb_total=0 et un résumé positif."""


def _build_documents_block(texts: dict[str, str], max_chars_per_doc: int) -> str:
    """Construit le bloc de texte formaté avec séparateurs clairs pour chaque document.

    Args:
        texts: Dictionnaire {doc_type: text_content}.
        max_chars_per_doc: Nombre maximum de caractères par document.

    Returns:
        Texte formaté avec séparateurs pour injection dans le prompt.
    """
    parts: list[str] = []

    for doc_type, content in texts.items():
        doc_label = doc_type.upper()

        # Tronquer si nécessaire
        if len(content) > max_chars_per_doc:
            content = content[:max_chars_per_doc] + "\n[... texte tronqué ...]"

        parts.append(
            f"{'=' * 60}\n"
            f"DOCUMENT : {doc_label}\n"
            f"{'=' * 60}\n"
            f"{content}\n"
        )

    return "\n".join(parts)


def detect_conflicts(
    texts: dict[str, str],
    project_id: str | None = None,
) -> dict[str, Any]:
    """Détecte les conflits et contradictions entre les pièces d'un DCE.

    Args:
        texts: Dictionnaire {doc_type: text_content}.
               Exemple : {"RC": "...", "CCTP": "...", "CCAP": "..."}
               Chaque texte sera tronqué a 16000 caracteres pour respecter
               la fenetre de contexte du LLM.
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire valide par ValidatedConflicts contenant :
        - conflicts: list[dict] — chaque conflit avec type, severite, docs, citations, etc.
        - nb_critiques: int — nombre de conflits de severite CRITIQUE
        - nb_total: int — nombre total de conflits detectes
        - resume: str — resume en 2-3 phrases
        - confidence_overall: float
        - model_used: str
        - documents_analyzed: list[str] — liste des types de documents analyses
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    if not texts:
        logger.warning(f"{log_prefix}Aucun texte fourni pour la détection de conflits")
        return {
            "conflicts": [],
            "nb_critiques": 0,
            "nb_total": 0,
            "resume": "Aucun document fourni pour l'analyse.",
            "confidence_overall": 0.0,
            "model_used": llm_service.get_model_name(),
            "documents_analyzed": [],
        }

    if len(texts) < 2:
        logger.warning(
            f"{log_prefix}Un seul document fourni ({list(texts.keys())}) — "
            f"la détection de conflits nécessite au moins 2 documents"
        )
        return {
            "conflicts": [],
            "nb_critiques": 0,
            "nb_total": 0,
            "resume": (
                f"Un seul document fourni ({list(texts.keys())[0]}). "
                "La détection de conflits nécessite au moins 2 documents à comparer."
            ),
            "confidence_overall": 0.0,
            "model_used": llm_service.get_model_name(),
            "documents_analyzed": list(texts.keys()),
        }

    # Tronquer chaque document à 16000 chars pour garder de la place
    # pour tous les docs dans le contexte LLM
    max_chars_per_doc = 16_000
    doc_types = list(texts.keys())

    total_chars_original = sum(len(t) for t in texts.values())
    documents_block = _build_documents_block(texts, max_chars_per_doc)
    total_chars_after = len(documents_block)

    if total_chars_original > total_chars_after:
        logger.warning(
            f"{log_prefix}Textes tronqués pour détection conflits : "
            f"{total_chars_original} -> {total_chars_after} caractères "
            f"({len(doc_types)} documents)"
        )

    user_prompt = CONFLICT_USER_PROMPT_TEMPLATE.format(documents_block=documents_block)

    logger.info(
        f"{log_prefix}Détection de conflits — "
        f"{len(doc_types)} documents ({', '.join(doc_types)}), "
        f"{total_chars_after} caractères"
    )

    try:
        result = llm_service.complete_json(
            system_prompt=CONFLICT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["conflicts"],
            validator=ValidatedConflicts,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM détection conflits (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM détection conflits inattendue: {exc}")
        raise

    # Post-traitement : recalculer les compteurs pour cohérence
    conflicts = result.get("conflicts", [])
    nb_critiques = sum(1 for c in conflicts if c.get("severity") == "CRITIQUE")
    nb_total = len(conflicts)

    # Corriger les compteurs si le LLM les a mal calculés
    if result.get("nb_critiques") != nb_critiques:
        logger.debug(
            f"{log_prefix}Correction nb_critiques : "
            f"LLM={result.get('nb_critiques')} -> réel={nb_critiques}"
        )
    if result.get("nb_total") != nb_total:
        logger.debug(
            f"{log_prefix}Correction nb_total : "
            f"LLM={result.get('nb_total')} -> réel={nb_total}"
        )

    result["nb_critiques"] = nb_critiques
    result["nb_total"] = nb_total

    # Trier les conflits par sévérité décroissante
    severity_order = {"CRITIQUE": 0, "HAUT": 1, "MOYEN": 2, "BAS": 3}
    result["conflicts"] = sorted(
        conflicts,
        key=lambda c: severity_order.get(c.get("severity", "MOYEN"), 2),
    )

    logger.info(
        f"{log_prefix}Conflits détectés — "
        f"{nb_total} total ({nb_critiques} critiques, "
        f"{sum(1 for c in conflicts if c.get('severity') == 'HAUT')} hauts, "
        f"{sum(1 for c in conflicts if c.get('severity') == 'MOYEN')} moyens, "
        f"{sum(1 for c in conflicts if c.get('severity') == 'BAS')} bas)"
    )

    result["model_used"] = llm_service.get_model_name()
    result["documents_analyzed"] = doc_types
    return result
