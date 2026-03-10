"""Enrichissement du score Go/No-Go par comparaison avec le profil entreprise.

9 dimensions d'évaluation :
  1. Capacité financière (CA vs exigences)
  2. Taille marché (montant vs capacité max)
  3. Certifications (couverture vs requises)
  4. Zone géographique (régions d'intervention)
  5. Adéquation assurance (RC Pro + décennale vs requis)
  6. Viabilité marge (marge estimée vs seuil minimum)
  7. Capacité charge (projets actifs vs max simultanés)
  8. Couverture sous-traitance (spécialités partenaires)
  9. Taux de succès historique (win rate estimé — bonus)

Ce module est purement synchrone (pas d'appel LLM) et peut être utilisé
depuis le worker Celery ou depuis un endpoint FastAPI via run_in_executor.
"""
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)


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

    # ── Dimension 5 : Adéquation assurance ────────────────────────────────
    assurance_rc = _parse_int(company_profile.get("assurance_rc_montant"))
    assurance_decennale = company_profile.get("assurance_decennale")

    assurance_score = 100
    if market_amount and assurance_rc is not None:
        if assurance_rc < market_amount:
            ratio = assurance_rc / market_amount
            assurance_score = int(min(90, 100 * ratio))
            gaps.append(
                f"RC Pro insuffisante : {assurance_rc:,} € vs montant marché {market_amount:,} €"
            )
        else:
            strengths.append(f"RC Pro ({assurance_rc:,} €) couvre le montant du marché")
    elif assurance_rc is None:
        assurance_score = 60  # Non renseigné

    if assurance_decennale is False:
        assurance_score = max(0, assurance_score - 30)
        gaps.append("Assurance décennale non souscrite")
    elif assurance_decennale is True:
        strengths.append("Assurance décennale active")

    dimension_scores["insurance_adequacy"] = assurance_score

    # ── Dimension 6 : Viabilité marge ────────────────────────────────────
    marge_min_pct = _parse_int(company_profile.get("marge_minimale_pct"))
    estimated_margin = gonogo_payload.get("estimated_margin_pct")

    margin_score = 80  # Par défaut neutre
    if marge_min_pct is not None and estimated_margin is not None:
        try:
            est_m = float(estimated_margin)
            if est_m < marge_min_pct:
                margin_score = int(max(0, 100 * est_m / marge_min_pct))
                gaps.append(
                    f"Marge estimée ({est_m:.0f}%) inférieure au seuil ({marge_min_pct}%)"
                )
            else:
                margin_score = 100
                strengths.append(
                    f"Marge estimée ({est_m:.0f}%) au-dessus du seuil ({marge_min_pct}%)"
                )
        except (ValueError, TypeError):
            pass
    elif marge_min_pct is None:
        margin_score = 70  # Non renseigné
    dimension_scores["margin_viability"] = margin_score

    # ── Dimension 7 : Capacité de charge (projets simultanés) ─────────────
    max_simultaneous = _parse_int(company_profile.get("max_projets_simultanes"))
    active_count = _parse_int(company_profile.get("projets_actifs_count"))

    capacity_score = 80
    if max_simultaneous is not None and active_count is not None:
        if active_count >= max_simultaneous:
            capacity_score = 10
            gaps.append(
                f"Capacité saturée : {active_count} projets actifs / {max_simultaneous} max"
            )
        elif active_count >= max_simultaneous * 0.8:
            capacity_score = 50
            gaps.append(
                f"Capacité presque saturée : {active_count}/{max_simultaneous} projets"
            )
        else:
            capacity_score = 100
            strengths.append(
                f"Capacité disponible : {active_count}/{max_simultaneous} projets"
            )
    elif max_simultaneous is None:
        capacity_score = 70  # Non renseigné
    dimension_scores["workload_capacity"] = capacity_score

    # ── Dimension 8 : Couverture sous-traitance ───────────────────────────
    partenaires: list[str] = company_profile.get("partenaires_specialites") or []
    all_specialties = set(s.lower() for s in company_specialties + partenaires)

    # Vérifier si les spécialités détectées dans le marché sont couvertes
    market_specialties: list[str] = gonogo_payload.get("required_specialties") or []
    partner_score = 100
    if market_specialties:
        market_specs_normalized = [s.lower().strip() for s in market_specialties]
        covered = sum(1 for s in market_specs_normalized if any(sp in s or s in sp for sp in all_specialties))
        partner_score = int(100 * covered / len(market_specs_normalized)) if market_specs_normalized else 100
        uncovered = [s for s in market_specialties if not any(sp in s.lower() or s.lower() in sp for sp in all_specialties)]
        if uncovered:
            gaps.append(f"Spécialités non couvertes : {', '.join(uncovered[:3])}")
        else:
            strengths.append("Toutes les spécialités requises couvertes (direct ou sous-traitance)")
    elif partenaires:
        strengths.append(f"{len(partenaires)} spécialité(s) partenaire(s) disponibles")
    dimension_scores["subcontracting_coverage"] = partner_score

    # ── Dimension 9 : Taux de succès historique (bonus) ───────────────────
    # Utilise les données de projets gagnés/perdus si disponibles dans le payload
    win_rate = gonogo_payload.get("historical_win_rate")
    history_score = 70  # Neutre par défaut
    if win_rate is not None:
        try:
            wr = float(win_rate)
            history_score = int(min(100, max(0, wr * 100)))
            if wr >= 0.3:
                strengths.append(f"Taux de succès historique : {wr:.0%}")
            elif wr < 0.15:
                gaps.append(f"Taux de succès faible : {wr:.0%}")
        except (ValueError, TypeError):
            pass
    dimension_scores["historical_success"] = history_score

    # ── Score global ────────────────────────────────────────────────────────
    # Pondérations sur 9 dimensions (somme = 1.00)
    weights = {
        "financial_capacity": 0.18,
        "market_size_fit": 0.14,
        "certifications": 0.16,
        "geographic_coverage": 0.08,
        "insurance_adequacy": 0.10,
        "margin_viability": 0.10,
        "workload_capacity": 0.10,
        "subcontracting_coverage": 0.08,
        "historical_success": 0.06,
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
