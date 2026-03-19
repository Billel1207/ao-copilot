"""Tests pour app/services/scoring_simulator.py — simulation de scoring."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.scoring_simulator import (
    simulate_scoring,
    _format_criteria_section,
    _format_company_section,
    SCORING_SYSTEM_PROMPT,
    SCORING_USER_PROMPT_TEMPLATE,
)


# ── Mock LLM response ───────────────────────────────────────────────────────

MOCK_SCORING_RESPONSE = {
    "dimensions": [
        {
            "criterion": "Valeur technique",
            "weight_pct": 60.0,
            "estimated_score": 14.0,
            "max_score": 20,
            "justification": "Bonne adéquation technique.",
            "tips_to_improve": ["Renforcer les références"],
        },
        {
            "criterion": "Prix",
            "weight_pct": 40.0,
            "estimated_score": 12.0,
            "max_score": 20,
            "justification": "Prix compétitif.",
            "tips_to_improve": ["Optimiser les coûts matériaux"],
        },
    ],
    "note_technique_estimee": 14.0,
    "note_financiere_estimee": 12.0,
    "note_globale_estimee": 13.2,
    "classement_probable": "Top 3",
    "axes_amelioration": [
        "Renforcer les références similaires",
        "Optimiser le planning",
    ],
    "resume": "Offre bien positionnée avec de bonnes chances.",
}

SAMPLE_CRITERIA = {
    "evaluation": {
        "eligibility_conditions": [
            {"condition": "CA > 1M EUR", "type": "hard"},
        ],
        "scoring_criteria": [
            {"criterion": "Valeur technique", "weight_percent": 60, "notes": "Mémoire technique"},
            {"criterion": "Prix", "weight_percent": 40, "notes": "DPGF"},
        ],
        "total_weight_check": 100,
        "confidence": 0.9,
    }
}

SAMPLE_COMPANY = {
    "company_name": "BTP Test SARL",
    "revenue_eur": 5_000_000,
    "employee_count": 50,
    "specialties": ["CVC", "Plomberie"],
    "certifications": ["Qualibat", "RGE"],
    "regions": ["Ile-de-France"],
    "years_experience": 15,
    "references_count": 25,
    "recent_references": [
        {"description": "Rénovation gymnase", "amount": "800000", "year": "2024"},
    ],
}


# ── _format_criteria_section() ───────────────────────────────────────────────

class TestFormatCriteriaSection:

    def test_with_full_criteria(self):
        result = _format_criteria_section(SAMPLE_CRITERIA)
        assert "Valeur technique" in result
        assert "60%" in result
        assert "ÉLIMINATOIRE" in result

    def test_with_empty_criteria(self):
        result = _format_criteria_section({})
        assert "Aucun critère" in result
        assert "Valeur technique (60%)" in result  # Default fallback

    def test_with_flat_criteria(self):
        """Criteria without 'evaluation' wrapper."""
        flat = {
            "eligibility_conditions": [],
            "scoring_criteria": [
                {"criterion": "Prix", "weight_percent": 100},
            ],
        }
        result = _format_criteria_section(flat)
        assert "Prix" in result

    def test_with_string_entries(self):
        """Criteria entries that are strings instead of dicts."""
        criteria = {
            "evaluation": {
                "eligibility_conditions": ["CA minimum requis"],
                "scoring_criteria": ["Valeur technique 60%"],
            }
        }
        result = _format_criteria_section(criteria)
        assert "CA minimum requis" in result


# ── _format_company_section() ────────────────────────────────────────────────

class TestFormatCompanySection:

    def test_with_full_profile(self):
        result = _format_company_section(SAMPLE_COMPANY)
        assert "BTP Test SARL" in result
        assert "5000000" in result or "5,000,000" in result or "5000000" in result
        assert "Qualibat" in result
        assert "Rénovation gymnase" in result

    def test_with_none_profile(self):
        result = _format_company_section(None)
        assert "Aucun profil" in result
        assert "candidat moyen" in result

    def test_with_empty_profile(self):
        result = _format_company_section({})
        # Should still have headers/footers
        assert "PROFIL ENTREPRISE" in result

    def test_with_list_specialties(self):
        profile = {"specialties": ["CVC", "Plomberie", "Électricité"]}
        result = _format_company_section(profile)
        assert "CVC" in result


# ── simulate_scoring() ──────────────────────────────────────────────────────

class TestSimulateScoring:

    @patch("app.services.scoring_simulator.llm_service")
    def test_basic_scoring(self, mock_llm):
        mock_llm.complete_json.return_value = MOCK_SCORING_RESPONSE
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)

        assert result["note_globale_estimee"] == 13.2
        assert result["classement_probable"] == "Top 3"
        assert result["model_used"] == "claude-test"
        assert result["has_company_profile"] is False
        assert len(result["dimensions"]) == 2

    @patch("app.services.scoring_simulator.llm_service")
    def test_with_company_profile(self, mock_llm):
        mock_llm.complete_json.return_value = MOCK_SCORING_RESPONSE
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA, company_profile=SAMPLE_COMPANY)

        assert result["has_company_profile"] is True

    @patch("app.services.scoring_simulator.llm_service")
    def test_with_project_id(self, mock_llm):
        mock_llm.complete_json.return_value = MOCK_SCORING_RESPONSE
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA, project_id="proj-123")
        assert result["note_globale_estimee"] > 0

    @patch("app.services.scoring_simulator.llm_service")
    def test_clamps_scores(self, mock_llm):
        """Scores above 20 should be clamped to 20."""
        response = {
            **MOCK_SCORING_RESPONSE,
            "note_technique_estimee": 25.0,
            "note_financiere_estimee": -5.0,
            "note_globale_estimee": 30.0,
        }
        mock_llm.complete_json.return_value = response
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)
        assert result["note_technique_estimee"] == 20.0
        assert result["note_financiere_estimee"] == 0.0
        assert result["note_globale_estimee"] == 20.0

    @patch("app.services.scoring_simulator.llm_service")
    def test_normalizes_invalid_classement(self, mock_llm):
        """Invalid classement values should be normalized."""
        response = {**MOCK_SCORING_RESPONSE, "classement_probable": "Favori"}
        mock_llm.complete_json.return_value = response
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)
        assert result["classement_probable"] == "Top 3"

    @patch("app.services.scoring_simulator.llm_service")
    def test_normalizes_risque_classement(self, mock_llm):
        response = {**MOCK_SCORING_RESPONSE, "classement_probable": "Situation risquée"}
        mock_llm.complete_json.return_value = response
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)
        assert result["classement_probable"] == "Risqué"

    @patch("app.services.scoring_simulator.llm_service")
    def test_normalizes_unknown_classement(self, mock_llm):
        response = {**MOCK_SCORING_RESPONSE, "classement_probable": "Something else"}
        mock_llm.complete_json.return_value = response
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)
        assert result["classement_probable"] == "Milieu de peloton"

    @patch("app.services.scoring_simulator.llm_service")
    def test_clamps_dimension_scores(self, mock_llm):
        response = {
            **MOCK_SCORING_RESPONSE,
            "dimensions": [
                {
                    "criterion": "Test",
                    "weight_pct": 150.0,
                    "estimated_score": 25.0,
                    "max_score": 20,
                    "justification": "test",
                    "tips_to_improve": [],
                },
            ],
        }
        mock_llm.complete_json.return_value = response
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring(SAMPLE_CRITERIA)
        dim = result["dimensions"][0]
        assert dim["estimated_score"] == 20.0
        assert dim["weight_pct"] == 100.0

    @patch("app.services.scoring_simulator.llm_service")
    def test_empty_criteria_still_works(self, mock_llm):
        mock_llm.complete_json.return_value = MOCK_SCORING_RESPONSE
        mock_llm.get_model_name.return_value = "claude-test"

        result = simulate_scoring({})
        assert result["classement_probable"] in {"Top 3", "Milieu de peloton", "Risqué"}

    @patch("app.services.scoring_simulator.llm_service")
    def test_llm_value_error_raised(self, mock_llm):
        mock_llm.complete_json.side_effect = ValueError("Invalid JSON")

        with pytest.raises(ValueError):
            simulate_scoring(SAMPLE_CRITERIA)

    @patch("app.services.scoring_simulator.llm_service")
    def test_llm_generic_error_raised(self, mock_llm):
        mock_llm.complete_json.side_effect = RuntimeError("API down")

        with pytest.raises(RuntimeError):
            simulate_scoring(SAMPLE_CRITERIA)


class TestScoringPrompts:
    """Verify prompt templates are well-defined."""

    def test_system_prompt_non_empty(self):
        assert len(SCORING_SYSTEM_PROMPT) > 100
        assert "scoring" in SCORING_SYSTEM_PROMPT.lower() or "notation" in SCORING_SYSTEM_PROMPT.lower()

    def test_user_prompt_template_has_placeholders(self):
        assert "{criteria_section}" in SCORING_USER_PROMPT_TEMPLATE
        assert "{company_section}" in SCORING_USER_PROMPT_TEMPLATE
