"""Enrichissement du score Go/No-Go par comparaison avec le profil entreprise.

Appelé après la génération du score LLM de base pour produire :
  - profile_match_score (0-100) : adéquation globale profil vs exigences
  - profile_gaps : liste des points manquants ou inadéquats

Ce module est purement synchrone (pas d'appel LLM) et peut être utilisé
depuis le worker Celery ou depuis un endpoint FastAPI via run_in_executor.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass
class ProfileMatchResult:
    """Résultat de la comparaison profil entreprise vs exigences du marché."""
    profile_match_score: int          # 0-100
    profile_gaps: list[str]           # Points manquants ou insuffisants
    profile_strengths: list[str]      # Points positifs identifiés
    dimension_scores: dict[str, int]  # Score par dimension (0-100 chacun)
    has_profile: bool = True          # False si aucun profil configuré


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_int(value: str | int | None) -> int | None:
    """Tente de parser une valeur en entier, retourne None si impossible."""
    if value is None:
        return None
    try:
        return int(str(value).replace(" ", "").replace("\xa0", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _region_match(company_regions: list[str], market_location: str | None) -> bool:
    """Vérifie si la localisation du marché est couverte par les régions de l'entreprise."""
    if not market_location or not company_regions:
        return True  # Pas d'info = pas de blocage
    loc_lower = market_location.lower()
    # Couverture nationale explicite
    if any("national" in r.lower() or "france" in r.lower() for r in company_regions):
        return True
    return any(r.lower() in loc_lower or loc_lower in r.lower() for r in company_regions)


def _normalize_certification(cert: str) -> str:
    return cert.strip().upper().replace("-", "").replace(" ", "")


def _certif_overlap(company_certs: list[str], required_certs: list[str]) -> tuple[int, list[str]]:
    """Retourne (% de certifications requises couvertes, liste des manquantes)."""
    if not required_certs:
        return 100, []
    company_normalized = {_normalize_certification(c) for c in company_certs}
    missing = []
    for rc in required_certs:
        if _normalize_certification(rc) not in company_normalized:
            missing.append(rc)
    pct = max(0, 100 - int(100 * len(missing) / len(required_certs)))
    return pct, missing


# ── Main function ─────────────────────────────────────────────────────────────

def compute_profile_match(
    company_profile: dict,
    gonogo_payload: dict,
    summary_payload: dict | None = None,
) -> ProfileMatchResult:
    """Compare le profil entreprise aux exigences extraites du DCE.

    Args:
        company_profile: Données de CompanyProfile (dict avec revenue_eur,
            employee_count, certifications, specialties, regions,
            max_market_size_eur).
        gonogo_payload: Payload Go/No-Go retourné par l'étape LLM (score,
            breakdown, etc.). Peut contenir des clés optionnelles :
            required_certifications, min_revenue_eur, market_amount_eur,
            market_location.
        summary_payload: Payload résumé (optionnel) — utilisé pour extraire
            la localisation et les montants estimés.

    Returns:
        ProfileMatchResult avec score 0-100 et listes de gaps/forces.
    """
    if not company_profile:
        logger.info("Aucun profil entreprise disponible — match non calculé")
        return ProfileMatchResult(
            profile_match_score=0,
            profile_gaps=["Aucun profil entreprise configuré"],
            profile_strengths=[],
            dimension_scores={},
            has_profile=False,
        )

    gaps: list[str] = []
    strengths: list[str] = []
    dimension_scores: dict[str, int] = {}

    company_revenue = _parse_int(company_profile.get("revenue_eur"))
    company_employees = _parse_int(company_profile.get("employee_count"))
    company_max_market = _parse_int(company_profile.get("max_market_size_eur"))
    company_certs: list[str] = company_profile.get("certifications") or []
    company_specialties: list[str] = company_profile.get("specialties") or []
    company_regions: list[str] = company_profile.get("regions") or []

    # Données extraites du marché (issues du Go/No-Go LLM ou du résumé)
    min_revenue_required = _parse_int(gonogo_payload.get("min_revenue_eur"))
    market_amount = _parse_int(gonogo_payload.get("market_amount_eur"))
    required_certs: list[str] = gonogo_payload.get("required_certifications") or []
    market_location: str | None = gonogo_payload.get("market_location")

    # Fallback localisation depuis le résumé
    if not market_location and summary_payload:
        overview = summary_payload.get("project_overview", {})
        market_location = overview.get("location") or overview.get("localisation")

    # ── Dimension 1 : CA vs exigences financières ──────────────────────────
    fin_score = 100
    if min_revenue_required and company_revenue is not None:
        if company_revenue < min_revenue_required:
            ratio = company_revenue / min_revenue_required
            fin_score = int(min(95, 100 * ratio))
            gaps.append(
                f"CA insuffisant : {company_revenue:,} € vs {min_revenue_required:,} € requis"
            )
        else:
            strengths.append(
                f"CA ({company_revenue:,} €) conforme au minimum requis ({min_revenue_required:,} €)"
            )
    elif company_revenue is None:
        fin_score = 50  # Inconnu
    dimension_scores["financial_capacity"] = fin_score

    # ── Dimension 2 : Taille max marché vs montant du marché ───────────────
    market_fit_score = 100
    if market_amount and company_max_market is not None:
        if company_max_market < market_amount:
            ratio = company_max_market / market_amount
            market_fit_score = int(min(95, 100 * ratio))
            gaps.append(
                f"Marché trop important : {market_amount:,} € vs votre max {company_max_market:,} €"
            )
        else:
            strengths.append(
                f"Taille du marché ({market_amount:,} €) dans votre capacité ({company_max_market:,} €)"
            )
    elif company_max_market is None:
        market_fit_score = 70  # Pas renseigné mais pas bloquant
    dimension_scores["market_size_fit"] = market_fit_score

    # ── Dimension 3 : Certifications ───────────────────────────────────────
    if required_certs:
        certif_score, missing_certs = _certif_overlap(company_certs, required_certs)
        dimension_scores["certifications"] = certif_score
        if missing_certs:
            gaps.append(
                f"Certifications manquantes : {', '.join(missing_certs)}"
            )
        else:
            strengths.append(
                f"Toutes les certifications requises sont présentes ({', '.join(required_certs[:3])})"
            )
    else:
        # Aucune certification spécifique requise
        dimension_scores["certifications"] = 100

    # ── Dimension 4 : Région d'intervention ────────────────────────────────
    if market_location:
        if _region_match(company_regions, market_location):
            dimension_scores["geographic_coverage"] = 100
            if company_regions:
                strengths.append(f"Zone géographique couverte ({market_location})")
        else:
            dimension_scores["geographic_coverage"] = 0
            gaps.append(
                f"Zone géographique non couverte : {market_location} "
                f"(vos régions : {', '.join(company_regions[:3]) or 'non renseignées'})"
            )
    else:
        dimension_scores["geographic_coverage"] = 80  # Pas d'info

    # ── Score global ────────────────────────────────────────────────────────
    # Pondérations : finances 30%, taille marché 25%, certifs 30%, région 15%
    weights = {
        "financial_capacity": 0.30,
        "market_size_fit": 0.25,
        "certifications": 0.30,
        "geographic_coverage": 0.15,
    }
    profile_match_score = int(sum(
        dimension_scores.get(dim, 100) * w
        for dim, w in weights.items()
    ))

    # Bornage 0-100
    profile_match_score = max(0, min(100, profile_match_score))

    logger.info(
        f"Profile match score={profile_match_score} | "
        f"gaps={len(gaps)} | strengths={len(strengths)}"
    )

    return ProfileMatchResult(
        profile_match_score=profile_match_score,
        profile_gaps=gaps,
        profile_strengths=strengths,
        dimension_scores=dimension_scores,
        has_profile=True,
    )


def enrich_gonogo_with_profile(
    gonogo_payload: dict,
    company_profile: dict | None,
    summary_payload: dict | None = None,
) -> dict:
    """Enrichit le payload Go/No-Go avec les données de matching profil.

    Ajoute les clés `profile_match_score`, `profile_gaps`, `profile_strengths`,
    `profile_dimension_scores` et `has_company_profile` au payload existant.

    Args:
        gonogo_payload: Payload original retourné par le LLM.
        company_profile: Dict du profil entreprise (peut être None).
        summary_payload: Payload résumé pour extraction de localisation (optionnel).

    Returns:
        Nouveau dict gonogo enrichi (ne modifie pas l'original).
    """
    enriched = dict(gonogo_payload)

    if not company_profile:
        enriched.update({
            "has_company_profile": False,
            "profile_match_score": None,
            "profile_gaps": [],
            "profile_strengths": [],
            "profile_dimension_scores": {},
        })
        return enriched

    result = compute_profile_match(company_profile, gonogo_payload, summary_payload)

    enriched.update({
        "has_company_profile": result.has_profile,
        "profile_match_score": result.profile_match_score,
        "profile_gaps": result.profile_gaps,
        "profile_strengths": result.profile_strengths,
        "profile_dimension_scores": result.dimension_scores,
    })

    return enriched
