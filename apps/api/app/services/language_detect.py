"""Détection automatique de la langue dominante des documents d'un projet.

Utilisé par le plan Europe et Business pour l'analyse bilingue FR/EN.
Approche hybride : heuristiques lexicales + ratio de mots-clés.
Pas de dépendance externe (pas besoin de langdetect/fasttext).
"""
import re
import structlog
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

# Mots-clés fortement indicatifs de la langue
_FR_MARKERS = {
    "marché", "acheteur", "candidat", "offre", "offres", "soumission",
    "appel", "consultation", "adjudicateur", "pouvoir", "règlement",
    "cahier", "clauses", "administratives", "techniques", "particulières",
    "pièces", "fournir", "attestation", "assurance", "garantie",
    "lot", "lots", "délai", "exécution", "travaux", "prestations",
    "notification", "attributaire", "titulaire", "entreprise",
    "et", "le", "la", "les", "de", "du", "des", "un", "une",
    "en", "dans", "pour", "sur", "par", "avec", "est", "sont",
    "qui", "que", "ce", "cette", "aux", "ou", "mais", "donc",
}

_EN_MARKERS = {
    "tender", "bidder", "contractor", "procurement", "contracting",
    "authority", "submission", "proposal", "evaluation", "criteria",
    "eligibility", "requirements", "documents", "certificate",
    "insurance", "guarantee", "lot", "deadline", "execution",
    "works", "services", "supplies", "framework", "agreement",
    "the", "and", "is", "are", "of", "in", "to", "for", "with",
    "that", "this", "from", "by", "on", "an", "at", "be", "has",
    "was", "were", "been", "have", "will", "shall", "must", "may",
}


def detect_language(text: str) -> str:
    """Détecte la langue dominante d'un texte.

    Returns:
        "fr" ou "en" (par défaut "fr" en cas d'ambiguïté)
    """
    if not text or len(text.strip()) < 50:
        return "fr"

    # Normaliser et tokeniser
    words = re.findall(r"\b[a-zàâäéèêëïîôùûüÿçœæ]+\b", text.lower())
    if not words:
        return "fr"

    total = len(words)
    fr_count = sum(1 for w in words if w in _FR_MARKERS)
    en_count = sum(1 for w in words if w in _EN_MARKERS)

    fr_ratio = fr_count / total
    en_ratio = en_count / total

    # Si le texte contient significativement plus de marqueurs anglais
    if en_ratio > fr_ratio * 1.5 and en_count > 20:
        return "en"

    return "fr"


def detect_project_language(db: Session, project_id: str) -> str:
    """Détecte la langue dominante de l'ensemble des documents d'un projet.

    Analyse les premiers 5000 caractères de chaque document et vote
    par majorité.

    Returns:
        "fr" ou "en"
    """
    import uuid
    from app.models.document import AoDocument, DocumentPage

    docs = db.query(AoDocument).filter_by(
        project_id=uuid.UUID(project_id),
        status="done",
    ).all()

    if not docs:
        return "fr"

    votes = {"fr": 0, "en": 0}

    for doc in docs:
        # Récupérer les premières pages pour échantillon
        pages = db.query(DocumentPage).filter_by(
            document_id=doc.id,
        ).order_by(DocumentPage.page_number).limit(5).all()

        sample_text = " ".join(p.text_content for p in pages if p.text_content)[:5000]
        lang = detect_language(sample_text)
        votes[lang] += 1

    detected = "en" if votes["en"] > votes["fr"] else "fr"
    logger.info(
        f"[{project_id}] Langue détectée : {detected} "
        f"(votes FR={votes['fr']}, EN={votes['en']})"
    )
    return detected
