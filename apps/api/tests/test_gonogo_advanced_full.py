"""Comprehensive tests for Go/No-Go advanced — 9-dimension profile matching.

Covers: all dimensions, edge cases, helpers, enrich_gonogo_with_profile.
"""
import pytest
from app.services.gonogo_advanced import (
    compute_profile_match,
    enrich_gonogo_with_profile,
    ProfileMatchResult,
    _parse_int,
    _region_match,
    _normalize_certification,
    _certif_overlap,
)


# ── Helper function tests ───────────────────────────────────────────────────

class TestParseInt:
    def test_none(self):
        assert _parse_int(None) is None

    def test_int_value(self):
        assert _parse_int(42) == 42

    def test_string_value(self):
        assert _parse_int("1000") == 1000

    def test_string_with_spaces(self):
        assert _parse_int("1 000 000") == 1000000

    def test_string_with_nbsp(self):
        assert _parse_int("5\xa0000") == 5000

    def test_string_with_comma(self):
        assert _parse_int("1,500") == 1500

    def test_invalid_string(self):
        assert _parse_int("abc") is None

    def test_empty_string(self):
        assert _parse_int("") is None


class TestRegionMatch:
    def test_no_location(self):
        assert _region_match(["PACA"], None) is True

    def test_no_regions(self):
        assert _region_match([], "Paris") is True

    def test_national_coverage(self):
        assert _region_match(["France entière"], "Marseille") is True

    def test_national_keyword(self):
        assert _region_match(["National"], "Lyon") is True

    def test_matching_region(self):
        assert _region_match(["Île-de-France", "PACA"], "île-de-france") is True

    def test_location_in_region(self):
        assert _region_match(["Île-de-France"], "paris") is True

    def test_no_match(self):
        assert _region_match(["Bretagne"], "Marseille") is False


class TestNormalizeCertification:
    def test_basic(self):
        assert _normalize_certification("ISO 9001") == "ISO9001"

    def test_with_dashes(self):
        assert _normalize_certification("Qualibat-2111") == "QUALIBAT2111"

    def test_lowercase_input(self):
        assert _normalize_certification("rge") == "RGE"


class TestCertifOverlap:
    def test_no_required(self):
        pct, missing = _certif_overlap(["ISO 9001"], [])
        assert pct == 100
        assert missing == []

    def test_all_present(self):
        pct, missing = _certif_overlap(["ISO 9001", "RGE"], ["ISO 9001", "RGE"])
        assert pct == 100
        assert missing == []

    def test_all_missing(self):
        pct, missing = _certif_overlap([], ["ISO 9001", "RGE"])
        assert pct == 0
        assert len(missing) == 2

    def test_partial_match(self):
        pct, missing = _certif_overlap(["ISO 9001"], ["ISO 9001", "RGE", "MASE"])
        # 2 missing out of 3 -> max(0, 100 - int(100*2/3)) = 100-66 = 34
        assert pct == 34
        assert "RGE" in missing
        assert "MASE" in missing

    def test_case_insensitive(self):
        pct, missing = _certif_overlap(["iso 9001"], ["ISO 9001"])
        assert pct == 100
        assert missing == []


# ── Dimension-specific tests ────────────────────────────────────────────────

class TestDimensionFinancialCapacity:
    def test_revenue_sufficient(self):
        result = compute_profile_match(
            {"revenue_eur": 5_000_000, "certifications": [], "regions": []},
            {"min_revenue_eur": 1_000_000},
        )
        assert result.dimension_scores["financial_capacity"] == 100
        assert any("CA" in s and "conforme" in s for s in result.profile_strengths)

    def test_revenue_insufficient(self):
        result = compute_profile_match(
            {"revenue_eur": 500_000, "certifications": [], "regions": []},
            {"min_revenue_eur": 2_000_000},
        )
        assert result.dimension_scores["financial_capacity"] < 100
        assert any("CA insuffisant" in g for g in result.profile_gaps)

    def test_revenue_unknown(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"min_revenue_eur": 1_000_000},
        )
        assert result.dimension_scores["financial_capacity"] == 50


class TestDimensionMarketSizeFit:
    def test_market_within_capacity(self):
        result = compute_profile_match(
            {"max_market_size_eur": 5_000_000, "certifications": [], "regions": []},
            {"market_amount_eur": 1_000_000},
        )
        assert result.dimension_scores["market_size_fit"] == 100

    def test_market_exceeds_capacity(self):
        result = compute_profile_match(
            {"max_market_size_eur": 500_000, "certifications": [], "regions": []},
            {"market_amount_eur": 2_000_000},
        )
        assert result.dimension_scores["market_size_fit"] < 100
        assert any("trop important" in g.lower() for g in result.profile_gaps)

    def test_market_size_not_set(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"market_amount_eur": 1_000_000},
        )
        assert result.dimension_scores["market_size_fit"] == 70


class TestDimensionInsurance:
    def test_rc_sufficient(self):
        result = compute_profile_match(
            {"assurance_rc_montant": 3_000_000, "assurance_decennale": True,
             "certifications": [], "regions": []},
            {"market_amount_eur": 1_000_000},
        )
        assert result.dimension_scores["insurance_adequacy"] == 100
        assert any("RC Pro" in s for s in result.profile_strengths)
        assert any("décennale" in s for s in result.profile_strengths)

    def test_rc_insufficient(self):
        result = compute_profile_match(
            {"assurance_rc_montant": 200_000, "certifications": [], "regions": []},
            {"market_amount_eur": 1_000_000},
        )
        assert result.dimension_scores["insurance_adequacy"] < 100
        assert any("RC Pro insuffisante" in g for g in result.profile_gaps)

    def test_no_decennale(self):
        result = compute_profile_match(
            {"assurance_decennale": False, "certifications": [], "regions": []},
            {},
        )
        assert any("décennale" in g.lower() for g in result.profile_gaps)

    def test_rc_not_set(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"market_amount_eur": 1_000_000},
        )
        assert result.dimension_scores["insurance_adequacy"] == 60


class TestDimensionMarginViability:
    def test_margin_above_threshold(self):
        result = compute_profile_match(
            {"marge_minimale_pct": 8, "certifications": [], "regions": []},
            {"estimated_margin_pct": 12.0},
        )
        assert result.dimension_scores["margin_viability"] == 100

    def test_margin_below_threshold(self):
        result = compute_profile_match(
            {"marge_minimale_pct": 10, "certifications": [], "regions": []},
            {"estimated_margin_pct": 5.0},
        )
        assert result.dimension_scores["margin_viability"] < 100
        assert any("marge" in g.lower() for g in result.profile_gaps)

    def test_margin_not_set(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["margin_viability"] == 70


class TestDimensionWorkloadCapacity:
    def test_capacity_available(self):
        result = compute_profile_match(
            {"max_projets_simultanes": 10, "projets_actifs_count": 3,
             "certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["workload_capacity"] == 100
        assert any("disponible" in s.lower() for s in result.profile_strengths)

    def test_capacity_saturated(self):
        result = compute_profile_match(
            {"max_projets_simultanes": 5, "projets_actifs_count": 5,
             "certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["workload_capacity"] == 10
        assert any("saturée" in g.lower() for g in result.profile_gaps)

    def test_capacity_almost_saturated(self):
        result = compute_profile_match(
            {"max_projets_simultanes": 10, "projets_actifs_count": 9,
             "certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["workload_capacity"] == 50

    def test_capacity_not_configured(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["workload_capacity"] == 70


class TestDimensionSubcontracting:
    def test_all_specialties_covered(self):
        result = compute_profile_match(
            {"specialties": ["electricite"], "partenaires_specialites": ["plomberie"],
             "certifications": [], "regions": []},
            {"required_specialties": ["electricite", "plomberie"]},
        )
        assert result.dimension_scores["subcontracting_coverage"] == 100

    def test_uncovered_specialties(self):
        result = compute_profile_match(
            {"specialties": [], "partenaires_specialites": [],
             "certifications": [], "regions": []},
            {"required_specialties": ["electricite", "plomberie"]},
        )
        assert result.dimension_scores["subcontracting_coverage"] == 0
        assert any("non couvertes" in g.lower() for g in result.profile_gaps)

    def test_no_required_specialties_with_partners(self):
        result = compute_profile_match(
            {"specialties": [], "partenaires_specialites": ["electricite"],
             "certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["subcontracting_coverage"] == 100
        assert any("partenaire" in s.lower() for s in result.profile_strengths)


class TestDimensionHistoricalSuccess:
    def test_good_win_rate(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"historical_win_rate": 0.4},
        )
        assert result.dimension_scores["historical_success"] == 40
        assert any("succès" in s.lower() for s in result.profile_strengths)

    def test_low_win_rate(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"historical_win_rate": 0.1},
        )
        assert result.dimension_scores["historical_success"] == 10
        assert any("faible" in g.lower() for g in result.profile_gaps)

    def test_no_win_rate(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {},
        )
        assert result.dimension_scores["historical_success"] == 70

    def test_invalid_win_rate(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {"historical_win_rate": "invalid"},
        )
        assert result.dimension_scores["historical_success"] == 70


class TestDimensionGeography:
    def test_location_from_summary_fallback(self):
        """When no market_location in gonogo, fall back to summary_payload."""
        result = compute_profile_match(
            {"certifications": [], "regions": ["France entière"]},
            {},
            summary_payload={"project_overview": {"location": "Rennes"}},
        )
        # "France entière" matches any location via national coverage
        assert result.dimension_scores["geographic_coverage"] == 100

    def test_no_location_info(self):
        result = compute_profile_match(
            {"certifications": [], "regions": ["PACA"]},
            {},
        )
        assert result.dimension_scores["geographic_coverage"] == 80


# ── Global score tests ──────────────────────────────────────────────────────

class TestGlobalScore:
    def test_score_bounded_0_100(self):
        result = compute_profile_match(
            {"certifications": [], "regions": []},
            {},
        )
        assert 0 <= result.profile_match_score <= 100

    def test_empty_profile_dict(self):
        """Empty dict is falsy for `if not company_profile` -> treated as no profile."""
        result = compute_profile_match({}, {})
        # Empty dict is falsy in Python, so the guard `if not company_profile` triggers
        assert result.has_profile is False
        assert result.profile_match_score == 0


# ── enrich_gonogo_with_profile ──────────────────────────────────────────────

class TestEnrichGonogoWithProfile:
    def test_no_company_profile(self):
        """When company_profile is None, should set has_company_profile=False."""
        result = enrich_gonogo_with_profile(
            gonogo_payload={"score": 75},
            company_profile=None,
        )
        assert result["has_company_profile"] is False
        assert result["profile_match_score"] is None
        assert result["profile_gaps"] == []
        assert result["profile_dimension_scores"] == {}
        # Original fields preserved
        assert result["score"] == 75

    def test_with_company_profile(self):
        """With a profile, should enrich with match data."""
        result = enrich_gonogo_with_profile(
            gonogo_payload={"score": 80},
            company_profile={
                "revenue_eur": 5_000_000,
                "certifications": ["ISO 9001"],
                "regions": ["PACA"],
            },
        )
        assert result["has_company_profile"] is True
        assert isinstance(result["profile_match_score"], int)
        assert isinstance(result["profile_gaps"], list)
        assert isinstance(result["profile_strengths"], list)
        assert isinstance(result["profile_dimension_scores"], dict)
        # Original payload is preserved
        assert result["score"] == 80

    def test_does_not_mutate_original(self):
        """enrich_gonogo_with_profile should not modify the original dict."""
        original = {"score": 70}
        enrich_gonogo_with_profile(original, None)
        assert "has_company_profile" not in original

    def test_with_summary_payload(self):
        """Summary payload should be forwarded to compute_profile_match."""
        result = enrich_gonogo_with_profile(
            gonogo_payload={},
            company_profile={"certifications": [], "regions": ["Normandie"]},
            summary_payload={"project_overview": {"location": "Caen"}},
        )
        # Should use location from summary for geographic check
        assert result["has_company_profile"] is True
        assert "geographic_coverage" in result["profile_dimension_scores"]
