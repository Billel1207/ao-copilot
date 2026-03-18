"""Tests for Go/No-Go advanced — 9-dimension profile matching."""
import pytest
from app.services.gonogo_advanced import compute_profile_match, ProfileMatchResult


class TestComputeProfileMatch:
    """Tests for profile matching logic."""

    def test_no_profile_returns_default(self):
        """Without company profile, should return has_profile=False."""
        result = compute_profile_match(
            company_profile=None,
            market_data={},
        )
        assert result.has_profile is False
        assert result.profile_match_score >= 0

    def test_full_match(self):
        """Company with all matching attributes should score high."""
        profile = {
            "ca_annuel": 10_000_000,
            "effectif": 50,
            "certifications": ["ISO 9001", "Qualibat 2111"],
            "regions": ["Île-de-France", "Hauts-de-France"],
            "assurance_rc_montant": 2_000_000,
            "assurance_decennale": True,
            "marge_minimale_pct": 8.0,
            "max_projets_simultanes": 10,
            "projets_actifs_count": 3,
            "partenaires_specialites": ["électricité", "plomberie"],
        }
        market = {
            "montant_estime": 500_000,
            "certifications_requises": ["ISO 9001"],
            "localisation": "Paris",
            "rc_pro_min": 1_000_000,
            "garantie_decennale_requise": True,
            "marge_estimee_pct": 12.0,
        }
        result = compute_profile_match(
            company_profile=profile,
            market_data=market,
        )
        assert result.has_profile is True
        assert result.profile_match_score >= 50
        assert isinstance(result.dimension_scores, dict)

    def test_missing_certifications_penalized(self):
        """Missing required certifications should lower the score."""
        profile = {
            "ca_annuel": 1_000_000,
            "effectif": 10,
            "certifications": [],
            "regions": ["Île-de-France"],
        }
        market = {
            "montant_estime": 200_000,
            "certifications_requises": ["ISO 9001", "Qualibat 2111", "RGE"],
        }
        result = compute_profile_match(
            company_profile=profile,
            market_data=market,
        )
        assert any("certification" in g.lower() for g in result.profile_gaps)

    def test_ca_too_small_flagged(self):
        """Market too large relative to CA should flag a gap."""
        profile = {
            "ca_annuel": 500_000,
            "effectif": 5,
            "certifications": [],
            "regions": [],
        }
        market = {
            "montant_estime": 2_000_000,
        }
        result = compute_profile_match(
            company_profile=profile,
            market_data=market,
        )
        assert result.profile_match_score < 70

    def test_dimension_scores_are_bounded(self):
        """All dimension scores should be 0-100."""
        profile = {
            "ca_annuel": 5_000_000,
            "effectif": 30,
            "certifications": ["ISO 9001"],
            "regions": ["PACA"],
        }
        market = {
            "montant_estime": 300_000,
        }
        result = compute_profile_match(
            company_profile=profile,
            market_data=market,
        )
        for name, score in result.dimension_scores.items():
            assert 0 <= score <= 100, f"Dimension {name} has score {score} out of range"

    def test_result_fields_present(self):
        """ProfileMatchResult should have all required fields."""
        result = compute_profile_match(
            company_profile={"ca_annuel": 1_000_000, "certifications": [], "regions": []},
            market_data={},
        )
        assert hasattr(result, "profile_match_score")
        assert hasattr(result, "profile_gaps")
        assert hasattr(result, "profile_strengths")
        assert hasattr(result, "dimension_scores")
        assert isinstance(result.profile_gaps, list)
        assert isinstance(result.profile_strengths, list)
