"""Analyse spécialisée du CCTP (Cahier des Clauses Techniques Particulières).

Le CCTP définit les spécifications techniques, matériaux, normes, méthodes
d'exécution et contrôles attendus dans un marché de travaux BTP.

8 catégories d'analyse :
1. Matériaux et fournitures (NF, CE, marques imposées)
2. Normes et DTU applicables (NF DTU, Eurocodes, RE 2020)
3. Conditions d'exécution (accès, horaires, coactivité, phasage)
4. Essais et contrôles (autocontrôle, externe, essais pression/béton)
5. Garanties spécifiques (parfait achèvement, biennale, décennale)
6. Risques techniques (géotechnique, amiante, plomb, pollution)
7. Documents d'exécution à fournir (DOE, DIUO, notes de calcul)
8. Clauses restrictives (marques imposées, certifications spécifiques)
"""
import structlog
from typing import Any

from app.services.ccag_travaux_2021 import get_ccag_context_for_analyzer
from app.services.llm import llm_service
from app.services.llm_validators import ValidatedCctpAnalysis

logger = structlog.get_logger(__name__)

# ── Prompt système spécialisé CCTP ──────────────────────────────────────────

_CCAG_CONTEXT_CCTP = get_ccag_context_for_analyzer("cctp")

CCTP_SYSTEM_PROMPT = f"""Tu es un ingénieur expert en BTP et construction, spécialisé dans l'analyse des Cahiers des Clauses Techniques Particulières (CCTP) de marchés publics français.

Tu analyses le CCTP pour identifier les exigences techniques, les normes applicables, les risques et les clauses restrictives qui impactent la réponse à l'appel d'offres.

Tu dois identifier avec précision les éléments suivants :

1. MATÉRIAUX ET FOURNITURES :
   - Matériaux spécifiés avec marques (NF, CE, marques propriétaires)
   - Si une marque est imposée sans « ou équivalent », signale le risque ANTICONCURRENTIEL (art. R2111-7 CCP)
   - Exigences de provenance (local, européen, certifié)
   - Fiches techniques à fournir avant exécution

2. NORMES ET DTU APPLICABLES :
   - NF DTU (ex: DTU 13.1 fondations, DTU 20.1 maçonnerie, DTU 43.1 étanchéité)
   - Eurocodes (structures, sismique)
   - RE 2020 / RT 2012 (performance énergétique)
   - Normes spécifiques (NF EN, ISO, réglementation incendie, PMR)
   - Détecte les normes OBSOLÈTES ou CONTRADICTOIRES

3. CONDITIONS D'EXÉCUTION :
   - Accès chantier (contraintes, horaires, riverains)
   - Coactivité avec d'autres entreprises
   - Phasage imposé (ordre des lots, interdépendances)
   - Conditions climatiques (périodes d'arrêt, intempéries)
   - Protection de l'existant (bâtiments, réseaux, végétation)

4. ESSAIS ET CONTRÔLES :
   - Essais à la charge du titulaire (béton, compactage, pression, étanchéité)
   - Autocontrôle vs contrôle externe
   - Plan d'assurance qualité (PAQ) exigé
   - Fréquence des essais, laboratoires agréés

5. GARANTIES SPÉCIFIQUES :
   - Garantie de parfait achèvement (GPA) — durée et conditions
   - Garantie biennale — équipements dissociables
   - Garantie décennale — solidité ouvrage
   - Extensions de garantie au-delà du CCAG

6. RISQUES TECHNIQUES :
   - Risque géotechnique (sol, nappe, karst, remblais)
   - Amiante, plomb, pollution des sols (diagnostics requis)
   - Réseaux enterrés (DICT obligatoire)
   - Démolition / désamiantage (plan de retrait)
   - Environnement protégé (ABF, zones humides, faune)

7. DOCUMENTS D'EXÉCUTION À FOURNIR :
   - DOE (Dossier des Ouvrages Exécutés)
   - DIUO (Dossier d'Intervention Ultérieure sur l'Ouvrage)
   - Notes de calcul (structures, thermique, acoustique)
   - Plans d'exécution, PV d'essais, fiches techniques
   - Délais de remise de ces documents

8. CLAUSES RESTRICTIVES :
   - Certifications spécifiques imposées (Qualibat, RGE, MASE, ISO)
   - Qualifications / habilitations obligatoires
   - Exclusivités fournisseur (contraire au CCP si non justifié)
   - Exigences disproportionnées (surcapacité, moyens excessifs)

{_CCAG_CONTEXT_CCTP}

9. CONTRADICTIONS TECHNIQUES INTERNES :
   - Détecte les contradictions internes au sein du même CCTP
   - Article A qui dit X tandis qu'un autre article B dit Y (incompatible)
   - Spécifications de matériaux contradictoires (ex: béton C25/30 à un endroit, C30/37 pour le même ouvrage ailleurs)
   - Références de normes incompatibles (ex: NF DTU obsolète vs Eurocode en vigueur pour le même lot)
   - Exigences de performances contradictoires (ex: résistance thermique incompatible avec épaisseur imposée)
   - Signale la sévérité : high (bloquant pour l'exécution), medium (source de litige), low (ambiguïté à clarifier)

Réponds UNIQUEMENT en JSON valide, sans commentaires ni texte autour.
Attribue un score de complexité technique de 0 à 100 :
  - 0-30  : chantier simple (petit entretien, peinture, nettoyage)
  - 31-60 : complexité moyenne (réhabilitation, second œuvre)
  - 61-80 : complexité haute (neuf multi-lots, VRD, génie civil)
  - 81-100 : très complexe (infrastructure, ouvrage d'art, nucléaire)
"""

CCTP_USER_PROMPT_TEMPLATE = """Analyse ce CCTP (Cahier des Clauses Techniques Particulières) et extrais toutes les informations techniques pertinentes.

--- TEXTE DU CCTP ---
{text}
--- FIN DU TEXTE ---

Réponds avec ce JSON exact :
{{
  "exigences_techniques": [
    {{
      "category": "materiaux|normes|execution|essais|garanties|risques|documents|restrictives",
      "description": "Description de l'exigence (1-2 phrases)",
      "norme_ref": "NF DTU XX.X ou Eurocode X ou null",
      "risk_level": "CRITIQUE|HAUT|MOYEN|BAS|INFO",
      "citation": "Extrait exact du CCTP (50-150 chars)",
      "conseil": "Recommandation pour la réponse (1 phrase)"
    }}
  ],
  "normes_dtu_applicables": [
    {{
      "code": "NF DTU XX.X ou EN XXXX ou ISO XXXX",
      "titre": "Titre de la norme",
      "applicabilite": "Quels lots/ouvrages sont concernés"
    }}
  ],
  "materiaux_imposes": [
    {{
      "designation": "Nom du matériau/produit",
      "marque_imposee": true,
      "anticoncurrentiel": true,
      "alternative": "si 'ou équivalent' mentionné, sinon null"
    }}
  ],
  "essais_controles": [
    {{
      "type": "Nature de l'essai (béton, compactage, pression, etc.)",
      "frequence": "Fréquence (tous les X m³, par lot, etc.)",
      "responsable": "titulaire|moa|moe|labo_externe"
    }}
  ],
  "documents_execution": [
    {{
      "type": "DOE|DIUO|notes_calcul|plans_exe|PAQ|fiches_techniques|PV_essais",
      "obligatoire": true,
      "delai": "Délai de remise si spécifié"
    }}
  ],
  "risques_techniques": [
    {{
      "type": "geotechnique|amiante|plomb|pollution|reseaux|demolition|environnement|autre",
      "severity": "CRITIQUE|HAUT|MOYEN|BAS",
      "description": "Description du risque (1-2 phrases)",
      "mitigation": "Mesure d'atténuation prévue ou recommandée"
    }}
  ],
  "contradictions_techniques": [
    {{
      "article_a": "Référence de l'article/section A (ex: 'Art. 3.2.1 Béton')",
      "article_b": "Référence de l'article/section B contradictoire",
      "description": "Description de la contradiction (1-2 phrases)",
      "severity": "high|medium|low"
    }}
  ],
  "score_complexite_technique": 0,
  "resume": "Résumé technique de 3-5 phrases (principaux enjeux, exigences clés, risques dominants)",
  "confidence_overall": 0.0
}}
"""


# ── Constantes ──────────────────────────────────────────────────────────────

_MAX_TEXT_LENGTH = 48_000  # ~12k tokens, laisse de la marge pour les prompts

_VALID_CATEGORIES = {
    "materiaux", "normes", "execution", "essais",
    "garanties", "risques", "documents", "restrictives",
}

_VALID_RISK_LEVELS = {"CRITIQUE", "HAUT", "MOYEN", "BAS", "INFO"}

_VALID_RISK_TYPES = {
    "geotechnique", "amiante", "plomb", "pollution",
    "reseaux", "demolition", "environnement", "autre",
}

_VALID_DOC_TYPES = {
    "DOE", "DIUO", "notes_calcul", "plans_exe",
    "PAQ", "fiches_techniques", "PV_essais", "autre",
}

_VALID_RESPONSABLES = {"titulaire", "moa", "moe", "labo_externe"}


def analyze_cctp(text: str, project_id: str | None = None) -> dict[str, Any]:
    """Analyse un CCTP et retourne les exigences techniques structurées.

    Args:
        text: Texte brut du CCTP.
        project_id: ID du projet (pour logging).

    Returns:
        Dict avec exigences_techniques, normes_dtu, matériaux, essais,
        documents, risques, score_complexite, resume, confidence.
    """
    pid = project_id or "unknown"

    if not text or len(text.strip()) < 100:
        logger.warning(f"[{pid}] CCTP trop court ({len(text)} chars) — analyse annulée")
        return _empty_result()

    # Truncate
    if len(text) > _MAX_TEXT_LENGTH:
        logger.info(f"[{pid}] CCTP tronqué de {len(text)} à {_MAX_TEXT_LENGTH} chars")
        text = text[:_MAX_TEXT_LENGTH]

    user_prompt = CCTP_USER_PROMPT_TEMPLATE.format(text=text)

    try:
        result = llm_service.complete_json(
            CCTP_SYSTEM_PROMPT,
            user_prompt,
            required_keys=["exigences_techniques"],
            validator=ValidatedCctpAnalysis,
        )
    except ValueError as exc:
        logger.error(f"[{pid}] Erreur validation CCTP: {exc}")
        raise
    except Exception as exc:
        logger.error(f"[{pid}] Erreur LLM CCTP inattendue: {exc}")
        raise

    # ── Post-processing ──────────────────────────────────────────────────

    # Normaliser les exigences techniques
    exigences = result.get("exigences_techniques", [])
    for ex in exigences:
        cat = str(ex.get("category", "")).lower().strip()
        ex["category"] = cat if cat in _VALID_CATEGORIES else "autre"

        rl = str(ex.get("risk_level", "INFO")).upper().strip()
        ex["risk_level"] = rl if rl in _VALID_RISK_LEVELS else "INFO"

    # Normaliser les matériaux — comptage anticoncurrentiel
    materiaux = result.get("materiaux_imposes", [])
    nb_anticoncurrentiel = sum(1 for m in materiaux if m.get("anticoncurrentiel"))

    # Normaliser les essais
    essais = result.get("essais_controles", [])
    for e in essais:
        resp = str(e.get("responsable", "")).lower().strip()
        e["responsable"] = resp if resp in _VALID_RESPONSABLES else "titulaire"

    # Normaliser les documents
    docs = result.get("documents_execution", [])
    for d in docs:
        dtype = str(d.get("type", "")).strip()
        if dtype not in _VALID_DOC_TYPES:
            d["type"] = "autre"

    # Normaliser les risques techniques
    risques = result.get("risques_techniques", [])
    for r in risques:
        rtype = str(r.get("type", "")).lower().strip()
        r["type"] = rtype if rtype in _VALID_RISK_TYPES else "autre"

        sev = str(r.get("severity", "MOYEN")).upper().strip()
        r["severity"] = sev if sev in _VALID_RISK_LEVELS else "MOYEN"

    nb_risques_critiques = sum(1 for r in risques if r.get("severity") == "CRITIQUE")
    nb_risques_hauts = sum(1 for r in risques if r.get("severity") == "HAUT")

    # Normaliser les contradictions techniques
    contradictions = result.get("contradictions_techniques", [])
    _valid_contradiction_severities = {"high", "medium", "low"}
    for c in contradictions:
        sev = str(c.get("severity", "medium")).lower().strip()
        c["severity"] = sev if sev in _valid_contradiction_severities else "medium"

    # Score de complexité — clamp 0-100
    score = result.get("score_complexite_technique", 50)
    score = max(0, min(100, int(score)))
    result["score_complexite_technique"] = score

    # Confidence
    confidence = result.get("confidence_overall", 0.5)
    confidence = max(0.0, min(1.0, float(confidence)))
    result["confidence_overall"] = confidence

    # Compteurs statistiques
    result["nb_exigences"] = len(exigences)
    result["nb_normes"] = len(result.get("normes_dtu_applicables", []))
    result["nb_materiaux_imposes"] = len(materiaux)
    result["nb_anticoncurrentiel"] = nb_anticoncurrentiel
    result["nb_essais"] = len(essais)
    result["nb_documents_requis"] = len(docs)
    result["nb_risques_techniques"] = len(risques)
    result["nb_risques_critiques"] = nb_risques_critiques
    result["nb_risques_hauts"] = nb_risques_hauts
    result["nb_contradictions"] = len(contradictions)
    result["nb_contradictions_high"] = sum(1 for c in contradictions if c.get("severity") == "high")
    result["model_used"] = llm_service.get_model_name()

    logger.info(
        f"[{pid}] CCTP analysé : {len(exigences)} exigences, {len(risques)} risques "
        f"({nb_risques_critiques} critiques), {len(contradictions)} contradictions, "
        f"score complexité {score}/100, "
        f"{nb_anticoncurrentiel} matériaux anticoncurrentiels"
    )

    return result


def _empty_result() -> dict[str, Any]:
    """Retourne un résultat vide en cas de texte insuffisant."""
    return {
        "exigences_techniques": [],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [],
        "documents_execution": [],
        "risques_techniques": [],
        "contradictions_techniques": [],
        "score_complexite_technique": 0,
        "resume": "Texte CCTP insuffisant pour analyse.",
        "confidence_overall": 0.0,
        "nb_exigences": 0,
        "nb_normes": 0,
        "nb_materiaux_imposes": 0,
        "nb_anticoncurrentiel": 0,
        "nb_essais": 0,
        "nb_documents_requis": 0,
        "nb_risques_techniques": 0,
        "nb_risques_critiques": 0,
        "nb_risques_hauts": 0,
        "nb_contradictions": 0,
        "nb_contradictions_high": 0,
        "model_used": "none",
    }
