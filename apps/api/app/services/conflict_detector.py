"""Détecteur de conflits et contradictions entre les pièces du DCE.

Compare les textes du RC, CCTP, CCAP (et autres documents) pour identifier :
- Contradictions de délais, quantités, montants
- Exigences contradictoires entre documents
- Clauses potentiellement illégales
- Incohérences de références croisées
- Dérogations au CCAG-Travaux 2021
"""
import structlog
from typing import Any

from app.services.ccag_travaux_2021 import get_ccag_context_for_analyzer
from app.services.llm import llm_service
from app.services.llm_validators import ValidatedConflicts

logger = structlog.get_logger(__name__)

# ── Prompt système expert juriste BTP ────────────────────────────────────────

_CCAG_CONTEXT_CONFLICT = get_ccag_context_for_analyzer("conflict")

CONFLICT_SYSTEM_PROMPT = f"""Tu es un juriste expert en droit des marchés publics français et en droit de la construction BTP.
Tu analyses plusieurs pièces d'un même DCE (Dossier de Consultation des Entreprises) pour détecter les CONTRADICTIONS et INCOHÉRENCES entre documents.

Dans un DCE, la hiérarchie des pièces contractuelles est généralement :
1. L'Acte d'Engagement (AE/ATTRI1)
2. Le CCAP (Cahier des Clauses Administratives Particulières)
3. Le CCTP (Cahier des Clauses Techniques Particulières)
4. Le RC (Règlement de Consultation)
5. Le BPU/DPGF (Bordereau des Prix Unitaires / Décomposition du Prix Global et Forfaitaire)

TYPES DE CONFLITS À DÉTECTER :

1. CONTRADICTIONS DE DÉLAIS (conflict_type: "delai") :
   - Le RC annonce un délai d'exécution différent du CCAP ou CCTP
   - Délai de remise des offres incohérent entre RC et avis de publicité
   - Délai de paiement différent entre AE et CCAP
   - Période de garantie contradictoire entre CCAP et CCTP
   EXEMPLES RÉELS :
   - RC : "délai d'exécution : 6 mois" vs CCAP : "durée des travaux : 180 jours ouvrés" → Conflit : 6 mois calendaires ≠ 180 jours ouvrés (~9 mois)
   - AE : "délai de paiement : 45 jours" vs CCAP : "le délai global de paiement est de 30 jours" → Conflit CRITIQUE (et 45j peut être illégal)
   - RC : "visite de site obligatoire le 15 mars" vs CCAP : "date limite des visites : 10 mars" → Conflit
   - CCTP : "travaux terminés avant le 31 décembre" vs CCAP : "délai d'exécution : 4 mois à compter de l'OS" → Potentiellement incohérent si OS tardif

2. CONTRADICTIONS DE QUANTITÉS OU MONTANTS (conflict_type: "montant") :
   - Quantités du DPGF/BPU ne correspondent pas aux descriptifs du CCTP
   - Montant estimé du marché différent entre RC et CCAP
   - Taux de pénalités différents entre CCAP et AE
   - Retenue de garantie : pourcentage contradictoire entre documents
   EXEMPLES RÉELS :
   - DPGF : "lot peinture : 150 m²" vs CCTP : "surfaces à peindre : 200 m² (plans en annexe)" → Conflit HAUT
   - CCAP : "pénalités : 1/1000 par jour" vs AE : "pénalités de retard : 500 €/jour" → Conflit (deux formules différentes)
   - RC : "montant estimé : 500 000 € HT" vs CCAP : "marché estimé entre 300 000 et 400 000 € HT" → Conflit

3. EXIGENCES CONTRADICTOIRES (conflict_type: "exigence") :
   - Le RC exige une certification non mentionnée dans le CCAP
   - Conditions de sous-traitance différentes entre RC et CCAP
   - Modalités de remise des offres contradictoires (papier vs électronique)
   - Variantes autorisées dans le RC mais interdites dans l'AE
   EXEMPLES RÉELS :
   - RC : "variantes autorisées" vs AE (article 3) : "les variantes ne sont pas autorisées" → Conflit CRITIQUE
   - RC : "certification Qualibat 7131 exigée" vs CCAP : aucune mention de certification technique → Conflit MOYEN
   - RC : "remise des offres par voie dématérialisée uniquement" vs CCAP : "les offres sont remises sous pli cacheté" → Conflit HAUT
   - RC : "sous-traitance limitée à 30% du marché" vs loi 1975 et CCAP silencieux → Conflit (restriction potentiellement illégale)

4. CLAUSES POTENTIELLEMENT ILLÉGALES (conflict_type: "clause_illegale") :
   - Pénalités de retard > 1/1000 du montant par jour (disproportionné)
   - Retenue de garantie > 5% (seuil légal loi du 16 juillet 1971)
   - Délai de paiement > 30 jours sans justification (ordonnance 2019-359)
   - Garantie à première demande pour marché < 100 000 EUR
   - Clause de résiliation unilatérale sans indemnisation
   - Avance forfaitaire refusée pour marché > 50 000 EUR HT (article R2191-3 CCP)

5. INCOHÉRENCES DE RÉFÉRENCES (conflict_type: "reference") :
   - Article du CCTP renvoyant à un article du CCAP qui n'existe pas
   - Norme technique citée mais version obsolète ou retirée
   - Annexe mentionnée mais absente du DCE
   EXEMPLES RÉELS :
   - CCTP : "conformément à l'article 14.3 du CCAP" mais le CCAP n'a que 12 articles → Conflit MOYEN
   - CCTP : "selon norme NF P 98-331 (2005)" → Version obsolète, remplacée par NF P 98-331:2021
   - CCAP : "voir annexe 3 — planning prévisionnel" mais aucune annexe 3 dans le DCE → Conflit MOYEN

6. DÉROGATIONS AU CCAG-TRAVAUX 2021 (conflict_type: "deviation_ccag") :
   Le CCAP peut déroger au CCAG, mais certaines dérogations sont DÉFAVORABLES au titulaire.
   Compare chaque clause au référentiel CCAG ci-dessous et signale les écarts.
   EXEMPLES RÉELS :
   - CCAG art. 19.1 : pénalités standard = 1/3000 par jour vs CCAP : "pénalités de 1/500 par jour" → CRITIQUE (5x plus sévère)
   - CCAG art. 14.3 : retenue ≤ 5% vs CCAP : "retenue de garantie de 10%" → CRITIQUE (illégal)
   - CCAG art. 11.6 : paiement 30 jours vs CCAP : "délai de paiement : 60 jours" → HAUT
   - CCAG art. 14.1 : avance 5% si > 50k€ vs CCAP : "il n'est pas prévu d'avance" → HAUT (potentiellement illégal)

{_CCAG_CONTEXT_CONFLICT}

7. CONTRADICTIONS CCTP ↔ DPGF/BPU (conflict_type: "cctp_dpgf") :
   Le DPGF/BPU doit refléter fidèlement les prescriptions du CCTP. Détecte :
   - Matériaux prescrits dans le CCTP mais absents ou différents dans le DPGF
   - Quantités incohérentes entre descriptif CCTP et métrés DPGF
   - Postes CCTP non chiffrés dans le DPGF (oublis)
   - Postes DPGF sans correspondance technique dans le CCTP
   - Spécifications techniques (normes, classes, performances) contradictoires
   EXEMPLES RÉELS :
   - CCTP : "menuiseries aluminium à rupture de pont thermique Uw ≤ 1.3" vs DPGF : "menuiseries PVC standard" → Conflit HAUT
   - CCTP : "200 m² de peinture glycéro" vs DPGF : "150 m² de peinture acrylique" → Conflit HAUT (type ET quantité)
   - CCTP prescrit "isolation ITE 140mm R=4.5" mais le DPGF ne comporte aucun poste ITE → Conflit CRITIQUE (poste oublié)
   - CCTP : "béton C35/45 XF3" vs DPGF : "béton C25/30" → Conflit HAUT (classe de résistance inférieure)

MÉTHODE DE COMPARAISON STRUCTURÉE :
Compare systématiquement chaque paire de documents :
- RC ↔ CCAP : délais, exigences candidature, critères attribution
- CCTP ↔ DPGF/BPU : matériaux, quantités, descriptions techniques, postes manquants
- CCAP ↔ AE : pénalités, garanties, prix, délais paiement
- CCTP ↔ CCAP : clauses techniques vs administratives, délais, normes
- Tous documents ↔ CCAG-Travaux 2021 : dérogations défavorables

Pour CHAQUE conflit détecté, fournis :
- conflict_type : "delai" | "montant" | "exigence" | "clause_illegale" | "reference" | "deviation_ccag"
- severity : "CRITIQUE" | "HAUT" | "MOYEN" | "BAS"
  * CRITIQUE : contradiction bloquante pouvant invalider le marché ou causer un litige majeur
  * HAUT : incohérence significative nécessitant une clarification avant soumission
  * MOYEN : ambiguïté à signaler dans les questions à l'acheteur
  * BAS : divergence mineure, probablement une erreur de rédaction
- doc_a : document source A (ex: "RC", "CCAP", "CCAG-Travaux")
- doc_b : document source B (ex: "CCTP", "DPGF")
- description : explication claire du conflit (2-3 phrases)
- citation_a : extrait du document A justifiant le conflit
- citation_b : extrait du document B montrant la contradiction
- recommendation : conseil actionnable (1-2 phrases)

RÈGLES IMPORTANTES :
- Ne signale PAS les différences normales de formulation entre documents (reformulations acceptables)
- Concentre-toi sur les contradictions SUBSTANTIELLES (chiffres, dates, exigences factuelles)
- Si un document est plus récent ou hiérarchiquement supérieur, mentionne-le dans la recommendation
- Pour les dérogations CCAG, utilise "CCAG-Travaux" comme doc_a et le document qui déroge comme doc_b
- Compte séparément les conflits CRITIQUES (nb_critiques) et le total (nb_total)

Réponds UNIQUEMENT en JSON valide sans commentaires ni texte autour."""

CONFLICT_USER_PROMPT_TEMPLATE = """Analyse ces pièces du même DCE et identifie TOUTES les contradictions, incohérences et dérogations CCAG entre documents.
Applique la méthode de comparaison structurée paire-à-paire.

{documents_block}

Réponds avec ce JSON exact :
{{
  "conflicts": [
    {{
      "conflict_type": "delai|montant|exigence|clause_illegale|reference|deviation_ccag|cctp_dpgf",
      "severity": "CRITIQUE|HAUT|MOYEN|BAS",
      "doc_a": "string (nom du document A ou CCAG-Travaux)",
      "doc_b": "string (nom du document B)",
      "description": "string (explication du conflit)",
      "citation_a": "string (extrait du document A ou article CCAG)",
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

    # Compter par type
    nb_deviation_ccag = sum(
        1 for c in conflicts if c.get("conflict_type") == "deviation_ccag"
    )

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
        f"{sum(1 for c in conflicts if c.get('severity') == 'BAS')} bas, "
        f"{nb_deviation_ccag} dérogations CCAG)"
    )

    result["model_used"] = llm_service.get_model_name()
    result["documents_analyzed"] = doc_types
    result["nb_deviation_ccag"] = nb_deviation_ccag
    return result
