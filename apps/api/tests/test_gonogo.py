"""Tests for Go/No-Go advanced — 9-dimension profile matching."""
import pytest
from app.services.gonogo_advanced import compute_profile_match, ProfileMatchResult


class TestComputeProfileMatch:
    """Tests for profile matching logic."""

    def test_no_profile_returns_default(self):
        """Without company profile, should return has_profile=False."""
        result = compute_profile_match(
            company_profile=None,
            gonogo_payload={},
        )
        assert result.has_profile is False
        assert result.profile_match_score >= 0

    def test_full_match(self):
        """Company with all matching attributes should score high."""
        profile = {
            "revenue_eur": 10_000_000,
            "employee_count": 50,
            "certifications": ["ISO 9001", "Qualibat 2111"],
            "regions": ["Île-de-France", "Hauts-de-France"],
            "max_market_size_eur": 5_000_000,
            "assurance_rc_montant": 2_000_000,
            "assurance_decennale": True,
            "marge_minimale_pct": 8,
            "max_projets_simultanes": 10,
            "projets_actifs_count": 3,
            "partenaires_specialites": ["électricité", "plomberie"],
            "specialties": [],
        }
        market = {
            "market_amount_eur": 500_000,
            "required_certifications": ["ISO 9001"],
            "market_location": "Paris",
            "min_revenue_eur": 1_000_000,
            "estimated_margin_pct": 12.0,
        }
        result = compute_profile_match(
            company_profile=profile,
            gonogo_payload=market,
        )
        assert result.has_profile is True
        assert result.profile_match_score >= 50
        assert isinstance(result.dimension_scores, dict)

    def test_missing_certifications_penalized(self):
        """Missing required certifications should lower the score."""
        profile = {
            "revenue_eur": 1_000_000,
            "employee_count": 10,
            "certifications": [],
            "regions": ["Île-de-France"],
        }
        market = {
            "market_amount_eur": 200_000,
            "required_certifications": ["ISO 9001", "Qualibat 2111", "RGE"],
        }
        result = compute_profile_match(
            company_profile=profile,
            gonogo_payload=market,
        )
        assert any("certification" in g.lower() for g in result.profile_gaps)

    def test_ca_too_small_flagged(self):
        """Market too large relative to CA should flag a gap."""
        profile = {
            "revenue_eur": 500_000,
            "employee_count": 5,
            "certifications": [],
            "regions": [],
            "max_market_size_eur": 500_000,
        }
        market = {
            "market_amount_eur": 2_000_000,
        }
        result = compute_profile_match(
            company_profile=profile,
            gonogo_payload=market,
        )
        assert result.profile_match_score < 80

    def test_dimension_scores_are_bounded(self):
        """All dimension scores should be 0-100."""
        profile = {
            "revenue_eur": 5_000_000,
            "employee_count": 30,
            "certifications": ["ISO 9001"],
            "regions": ["PACA"],
        }
        market = {
            "market_amount_eur": 300_000,
        }
        result = compute_profile_match(
            company_profile=profile,
            gonogo_payload=market,
        )
        for name, score in result.dimension_scores.items():
            assert 0 <= score <= 100, f"Dimension {name} has score {score} out of range"

    def test_result_fields_present(self):
        """ProfileMatchResult should have all required fields."""
        result = compute_profile_match(
            company_profile={"revenue_eur": 1_000_000, "certifications": [], "regions": []},
            gonogo_payload={},
        )
        assert hasattr(result, "profile_match_score")
        assert hasattr(result, "profile_gaps")
        assert hasattr(result, "profile_strengths")
        assert hasattr(result, "dimension_scores")
        assert isinstance(result.profile_gaps, list)
        assert isinstance(result.profile_strengths, list)
