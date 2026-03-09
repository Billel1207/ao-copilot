"""Routes de base de connaissances BTP — glossaire, seuils réglementaires, certifications."""
import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.btp_knowledge import (
    BTP_GLOSSARY,
    CCAP_RISK_RULES,
    MARKET_THRESHOLDS,
    CPV_BTP_CODES,
    CERTIFICATION_MAPPING,
    get_relevant_glossary_terms,
    check_market_threshold,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


# ── Glossaire ──────────────────────────────────────────────────────────────

@router.get("/glossary")
async def list_glossary(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retourne tous les termes du glossaire BTP avec leurs définitions."""
    terms = [
        {"term": term, "definition": definition}
        for term, definition in sorted(BTP_GLOSSARY.items(), key=lambda x: x[0].lower())
    ]
    return {
        "total": len(terms),
        "terms": terms,
    }


@router.get("/glossary/{term}")
async def get_glossary_term(
    term: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retourne la définition d'un terme BTP spécifique."""
    # Recherche exacte (insensible à la casse)
    matched_term = None
    matched_def = None
    for t, d in BTP_GLOSSARY.items():
        if t.lower() == term.lower():
            matched_term = t
            matched_def = d
            break

    if not matched_term:
        # Recherche partielle si pas de correspondance exacte
        partials = [
            {"term": t, "definition": d}
            for t, d in BTP_GLOSSARY.items()
            if term.lower() in t.lower()
        ]
        if partials:
            return {
                "found": False,
                "query": term,
                "suggestions": partials[:5],
                "message": f"Terme exact '{term}' non trouvé. Suggestions ci-dessous.",
            }
        raise HTTPException(
            status_code=404,
            detail=f"Terme '{term}' introuvable dans le glossaire BTP.",
        )

    return {
        "found": True,
        "term": matched_term,
        "definition": matched_def,
    }


# ── Seuils réglementaires ─────────────────────────────────────────────────

@router.get("/thresholds")
async def get_thresholds(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retourne les seuils réglementaires des marchés publics français 2024."""
    return {
        "year": 2024,
        "country": "France",
        "currency": "EUR",
        "thresholds": MARKET_THRESHOLDS,
        "ccap_risk_rules": CCAP_RISK_RULES,
    }


@router.get("/thresholds/check/{amount}")
async def check_threshold(
    amount: int,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Détermine le type de procédure applicable pour un montant donné en euros HT."""
    if amount < 0:
        raise HTTPException(status_code=400, detail="Le montant doit être positif.")

    procedure_text = check_market_threshold(amount)
    return {
        "amount_ht_eur": amount,
        "procedure": procedure_text,
    }


# ── Certifications ────────────────────────────────────────────────────────

@router.get("/certifications")
async def list_certifications(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retourne la liste des certifications et qualifications BTP reconnues."""
    certs = [
        {"name": name, "description": desc}
        for name, desc in sorted(CERTIFICATION_MAPPING.items(), key=lambda x: x[0].lower())
    ]
    return {
        "total": len(certs),
        "certifications": certs,
    }


# ── CPV Codes ─────────────────────────────────────────────────────────────

@router.get("/cpv")
async def list_cpv_codes(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retourne les codes CPV courants dans le secteur BTP."""
    codes = [
        {"code": code, "label": label}
        for code, label in sorted(CPV_BTP_CODES.items())
    ]
    return {
        "total": len(codes),
        "cpv_codes": codes,
    }


# ── Analyse textuelle ─────────────────────────────────────────────────────

@router.post("/glossary/extract")
async def extract_terms_from_text(
    body: dict,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Identifie les termes BTP présents dans un texte et retourne leurs définitions."""
    text = body.get("text", "")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Le champ 'text' est requis.")
    if len(text) > 50_000:
        raise HTTPException(status_code=400, detail="Le texte ne doit pas dépasser 50 000 caractères.")

    found = get_relevant_glossary_terms(text)
    return {
        "terms_found": len(found),
        "terms": [{"term": t, "definition": d} for t, d in found.items()],
    }
