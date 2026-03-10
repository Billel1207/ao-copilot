"""Vérificateur DC1/DC2 et attestations administratives requises dans un DCE.

Analyse le texte extrait du dossier de consultation pour identifier
TOUS les documents administratifs obligatoires (formulaires DC1/DC2,
attestations fiscales, URSSAF, assurances, Kbis, certifications, etc.)
et génère des alertes en cas de version périmée ou de délai de validité.

Inclut un pré-traitement OCR fuzzy pour normaliser les références
garbled par des scans de mauvaise qualité (ex: "D C1" → "DC1").
"""
import structlog
import re
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedDcCheck

logger = structlog.get_logger(__name__)


# ── Normalisation OCR pour références administratives ────────────────────

# Patterns regex pour corriger les erreurs OCR courantes sur les références
# administratives BTP. L'OCR sur PDFs scannés produit souvent des espaces
# parasites, des confusions de caractères (l/1, I/1, O/0), etc.
DC_FUZZY_PATTERNS: list[tuple[str, str]] = [
    # DC1 : espaces, confusions I/1/l
    (r"\bD\s*C\s*[1lI]\b", "DC1"),
    (r"\bDC[lI]\b", "DC1"),
    (r"\bD\s*C\s*1\b", "DC1"),
    # DC2
    (r"\bD\s*C\s*2\b", "DC2"),
    # DC3
    (r"\bD\s*C\s*3\b", "DC3"),
    # DC4
    (r"\bD\s*C\s*4\b", "DC4"),
    # ATTRI1
    (r"\bA\s*T\s*T\s*R\s*I\s*[1lI]\b", "ATTRI1"),
    (r"\bATTR[lI][1lI]?\b", "ATTRI1"),
    # NOTI1 / NOTI2
    (r"\bN\s*O\s*T\s*I\s*[1lI]\b", "NOTI1"),
    (r"\bN\s*O\s*T\s*I\s*2\b", "NOTI2"),
    # Kbis
    (r"\bK\s*[bB]\s*[iI1l]\s*[sS]\b", "Kbis"),
    (r"\bK\s*B\s*I\s*S\b", "Kbis"),
    # URSSAF
    (r"\bU\s*R\s*S\s*S\s*A\s*F\b", "URSSAF"),
    (r"\bURSSAE\b", "URSSAF"),  # F→E confusion OCR
    # Qualibat
    (r"\bQ\s*u\s*a\s*l\s*i\s*b\s*a\s*t\b", "Qualibat"),
    (r"\bQua[lI1]ibat\b", "Qualibat"),
    # Qualifelec
    (r"\bQ\s*u\s*a\s*l\s*i\s*f\s*e\s*l\s*e\s*c\b", "Qualifelec"),
    # ISO
    (r"\bI\s*S\s*O\s+(\d{4,5})\b", r"ISO \1"),
    # DUME
    (r"\bD\s*U\s*M\s*E\b", "DUME"),
    # MPS
    (r"\bM\s*P\s*S\b", "MPS"),
    # AGEFIPH
    (r"\bA\s*G\s*E\s*F\s*I\s*P\s*H\b", "AGEFIPH"),
    # RGE
    (r"\bR\s*G\s*E\b", "RGE"),
    # MASE
    (r"\bM\s*A\s*S\s*E\b", "MASE"),
]


def normalize_ocr_references(text: str) -> str:
    """Normalise les références administratives garblées par l'OCR.

    Corrige les erreurs OCR courantes (espaces parasites, confusions
    de caractères) pour les acronymes BTP/marchés publics.

    Args:
        text: Texte brut potentiellement garblé par OCR.

    Returns:
        Texte avec les références normalisées.
    """
    normalized = text
    corrections_count = 0

    for pattern, replacement in DC_FUZZY_PATTERNS:
        new_text = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        if new_text != normalized:
            corrections_count += 1
            normalized = new_text

    if corrections_count > 0:
        logger.info(
            f"OCR normalization: {corrections_count} corrections appliquées "
            f"sur les références administratives"
        )

    return normalized

# ── Prompt système expert marchés publics ────────────────────────────────────

DC_CHECK_SYSTEM_PROMPT = """Tu es un expert en marchés publics français, spécialisé dans la constitution des dossiers de candidature BTP.
Tu analyses des DCE (Dossiers de Consultation des Entreprises) pour identifier EXHAUSTIVEMENT tous les documents administratifs requis.

Tu dois repérer et lister CHAQUE document exigé, en t'appuyant sur ta connaissance approfondie du Code de la commande publique (articles R2143-3 à R2143-16) et des pratiques courantes des acheteurs publics français.

DOCUMENTS À IDENTIFIER :

1. FORMULAIRES OFFICIELS :
   - DC1 (Lettre de candidature) — version en vigueur 2024. ALERTE si le DCE mentionne une version antérieure (2016, 2019).
   - DC2 (Déclaration du candidat individuel ou du membre du groupement) — version en vigueur 2024. ALERTE si version périmée.
   - DC3 (Acte d'engagement) — si exigé séparément du formulaire ATTRI1.
   - DC4 (Déclaration de sous-traitance) — si la sous-traitance est envisagée.
   - ATTRI1 (Acte d'engagement) — le formulaire ATTRI1 remplace progressivement le DC3.
   - NOTI1, NOTI2 — formulaires de notification si mentionnés.
   - MPS (Marché Public Simplifié) — si le DCE autorise la candidature via MPS/DUME.
   - DUME (Document Unique de Marché Européen) — si marché au-dessus des seuils européens.

2. ATTESTATIONS FISCALES :
   - Attestation de régularité fiscale (impôts sur le revenu / IS + TVA)
   - Liasse 3666 ou équivalent en ligne (impots.gouv.fr)
   - Validité : année fiscale en cours ou N-1

3. ATTESTATION URSSAF (ou MSA pour régime agricole) :
   - Attestation de vigilance (article L.8222-1 du Code du travail)
   - Validité : 6 mois à compter de la date de délivrance
   - ALERTE si le DCE exige une attestation datant de moins de 3 mois (pratique courante mais vérifier)

4. ASSURANCES :
   - Attestation d'assurance responsabilité civile professionnelle — quasi systématique
   - Attestation d'assurance décennale (obligatoire si marché de travaux, article 1792 du Code civil)
   - Vérifier montants de couverture si précisés dans le DCE

5. KBIS OU ÉQUIVALENT :
   - Extrait Kbis ou extrait d'inscription au RCS/RM (moins de 3 mois)
   - Carte d'identification artisan (pour inscrits à la Chambre des Métiers)
   - Récépissé de dépôt au CFE pour les auto-entrepreneurs
   - Pour les associations : récépissé de déclaration en préfecture + statuts

6. CERTIFICATIONS ET QUALIFICATIONS :
   - Qualibat (avec numéro et domaine de qualification)
   - Qualifelec (électricité)
   - ISO 9001, ISO 14001, ISO 45001
   - MASE (Manuel d'Amélioration Sécurité des Entreprises)
   - RGE (Reconnu Garant de l'Environnement) — si travaux d'efficacité énergétique
   - Certifications spécifiques mentionnées (APSAD, COFRAC, etc.)

7. AUTRES DOCUMENTS FRÉQUENTS :
   - Attestation sur l'honneur (article R2143-3 CCP) : absence d'exclusion, régularité fiscale et sociale
   - Pouvoir de la personne habilitée à engager le candidat
   - Références de marchés similaires (3 dernières années)
   - Chiffre d'affaires des 3 derniers exercices
   - Effectifs moyens annuels
   - Certificats de capacité ou d'aptitude professionnelle
   - Attestation d'emploi de travailleurs handicapés (AGEFIPH) si > 20 salariés
   - Attestation de lutte contre le travail dissimulé

Pour CHAQUE document identifié, fournis :
- document : nom du document (ex: "DC1 v2024", "Attestation URSSAF", "Kbis")
- obligatoire : true/false
- date_validite : date d'expiration si connue ou déductible (format ISO YYYY-MM-DD), sinon null
- statut : "À_FOURNIR" (par défaut — l'entreprise doit le produire), "NON_REQUIS" (si explicitement non demandé)
- details : précisions utiles (version requise, montant de couverture, etc.)
- citations : extraits du DCE justifiant l'exigence [{doc, page, quote}]

ALERTES à générer (liste alertes) :
- Version périmée de formulaire (DC1/DC2 avant 2024)
- Délai de validité URSSAF trop court
- Assurance décennale demandée alors que ce ne sont pas des travaux
- Kbis de plus de 3 mois exigé mais non disponible
- Certification très spécifique potentiellement bloquante
- Exigence disproportionnée par rapport à la taille du marché

Réponds UNIQUEMENT en JSON valide sans commentaires ni texte autour."""

DC_CHECK_USER_PROMPT_TEMPLATE = """Analyse ce DCE et identifie TOUS les documents administratifs requis pour constituer le dossier de candidature.

--- TEXTE DU DCE ---
{text}
--- FIN DU TEXTE ---

Réponds avec ce JSON exact :
{{
  "documents_requis": [
    {{
      "document": "string (nom du document)",
      "obligatoire": true,
      "date_validite": "YYYY-MM-DD ou null",
      "statut": "À_FOURNIR|NON_REQUIS",
      "details": "string",
      "citations": [{{"doc": "string", "page": 0, "quote": "string"}}]
    }}
  ],
  "formulaires_obligatoires": ["DC1 v2024", "DC2 v2024"],
  "attestations_fiscales": true,
  "attestation_urssaf": true,
  "attestation_assurance_rc": true,
  "attestation_assurance_decennale": false,
  "kbis_requis": true,
  "certifications_requises": ["Qualibat 1312", "ISO 9001"],
  "alertes": [
    "Le DCE mentionne le DC1 version 2016 — version périmée, utiliser la version 2024",
    "Attestation URSSAF exigée de moins de 3 mois (plus restrictif que les 6 mois réglementaires)"
  ],
  "resume": "string (2-3 phrases résumant les exigences administratives)",
  "confidence_overall": 0.85
}}

Si le texte ne contient aucune exigence administrative identifiable, retourne des listes vides et confidence basse."""


def analyze_dc_requirements(text: str, project_id: str | None = None) -> dict[str, Any]:
    """Analyse un DCE et retourne la liste exhaustive des documents administratifs requis.

    Args:
        text: Texte extrait du DCE (RC, CCAP, ou documents combinés).
              Sera tronqué a 48000 caracteres si necessaire.
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire valide par ValidatedDcCheck contenant :
        - documents_requis: list[dict] — chaque document avec statut, validite, etc.
        - formulaires_obligatoires: list[str] — DC1, DC2, ATTRI1, etc.
        - attestations_fiscales: bool
        - attestation_urssaf: bool
        - attestation_assurance_rc: bool
        - attestation_assurance_decennale: bool
        - kbis_requis: bool
        - certifications_requises: list[str]
        - alertes: list[str] — alertes importantes (versions perimees, etc.)
        - resume: str
        - confidence_overall: float
        - model_used: str
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    # Pré-traitement : normaliser les références OCR garblées
    text = normalize_ocr_references(text)

    # Tronquer le texte si trop long (~12 000 tokens = ~48 000 chars)
    max_chars = 48_000
    if len(text) > max_chars:
        logger.warning(
            f"{log_prefix}Texte DCE tronqué pour DC check : {len(text)} -> {max_chars} caractères"
        )
        text = text[:max_chars] + "\n[... texte tronqué pour analyse ...]"

    user_prompt = DC_CHECK_USER_PROMPT_TEMPLATE.format(text=text)

    logger.info(f"{log_prefix}Analyse DC1/DC2 + attestations — {len(text)} caractères")

    try:
        result = llm_service.complete_json(
            system_prompt=DC_CHECK_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["documents_requis"],
            validator=ValidatedDcCheck,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM DC check (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM DC check inattendue: {exc}")
        raise

    # Post-traitement : compteurs et enrichissement
    documents = result.get("documents_requis", [])
    nb_obligatoires = sum(1 for d in documents if d.get("obligatoire", False))
    nb_alertes = len(result.get("alertes", []))

    # Enrichir les certifications depuis les documents si pas déjà rempli
    certifications = result.get("certifications_requises", [])
    for doc in documents:
        doc_name = doc.get("document", "").lower()
        if any(kw in doc_name for kw in ("qualibat", "qualifelec", "iso", "mase", "rge", "apsad")):
            cert_name = doc.get("document", "")
            if cert_name and cert_name not in certifications:
                certifications.append(cert_name)
    result["certifications_requises"] = certifications

    logger.info(
        f"{log_prefix}DC check terminé — "
        f"{len(documents)} documents identifiés ({nb_obligatoires} obligatoires), "
        f"{len(certifications)} certifications, {nb_alertes} alertes"
    )

    result["model_used"] = llm_service.get_model_name()
    return result
