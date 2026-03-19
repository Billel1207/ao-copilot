"""Tests for questions generator — mock LLM."""
import pytest
from unittest.mock import patch


SAMPLE_DCE_CONTEXT = """
Le CCTP mentionne un béton C30/37 mais le DPGF indique C25/30.
L'étude géotechnique n'est pas fournie dans le dossier.
Le délai d'exécution est de 4 mois pour un bâtiment de 2000 m².
Aucune précision sur les conditions d'accès au chantier.
"""

MOCK_QUESTIONS_RESPONSE = {
    "questions": [
        {
            "question": "Pourriez-vous confirmer la classe de béton requise pour les fondations ? Le CCTP article 3.1 mentionne un C30/37 XF3 tandis que le DPGF poste 2.1 indique un C25/30.",
            "context": "La différence de classe de résistance impacte significativement le chiffrage (environ +15% sur le poste béton).",
            "priority": "CRITIQUE",
            "related_doc": "CCTP / DPGF",
            "related_article": "CCTP Art. 3.1 / DPGF poste 2.1",
        },
        {
            "question": "L'étude géotechnique de type G2 AVP est-elle disponible ? Le CCTP y fait référence mais elle ne figure pas dans les pièces du DCE.",
            "context": "L'absence d'étude de sol empêche le dimensionnement précis des fondations.",
            "priority": "HAUTE",
            "related_doc": "CCTP",
            "related_article": "CCTP Art. 2.3",
        },
        {
            "question": "Quelles sont les conditions d'accès au chantier (horaires, contraintes riverains, zone de stockage) ?",
            "context": "Ces informations sont nécessaires pour l'organisation du chantier et l'estimation des coûts logistiques.",
            "priority": "MOYENNE",
            "related_doc": "CCTP",
            "related_article": "Non précisé",
        },
    ],
    "resume": "Principales zones d'ombre : contradiction béton CCTP/DPGF, étude de sol manquante, accès chantier non précisé.",
}


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_basic(mock_llm):
    """Test basic question generation."""
    mock_llm.complete_json_with_thinking.return_value = MOCK_QUESTIONS_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.questions_generator import generate_questions

    result = generate_questions(SAMPLE_DCE_CONTEXT, project_id="test-q")

    assert isinstance(result, dict)
    assert len(result["questions"]) == 3
    assert result["question_count"] == 3
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"
    assert "resume" in result


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_sorted_by_priority(mock_llm):
    """Test that questions are sorted by priority descending."""
    mock_llm.complete_json_with_thinking.return_value = {
        "questions": [
            {"question": "Q1", "context": "", "priority": "MOYENNE", "related_doc": "", "related_article": ""},
            {"question": "Q2", "context": "", "priority": "CRITIQUE", "related_doc": "", "related_article": ""},
            {"question": "Q3", "context": "", "priority": "HAUTE", "related_doc": "", "related_article": ""},
            {"question": "Q4", "context": "", "priority": "BASSE", "related_doc": "", "related_article": ""},
        ],
        "resume": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.questions_generator import generate_questions

    result = generate_questions("Contexte DCE.")

    priorities = [q["priority"] for q in result["questions"]]
    assert priorities == ["CRITIQUE", "HAUTE", "MOYENNE", "BASSE"]


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_with_summary(mock_llm):
    """Test question generation with summary payload."""
    mock_llm.complete_json_with_thinking.return_value = {
        "questions": [
            {"question": "Q1", "context": "c", "priority": "HAUTE", "related_doc": "RC", "related_article": "Art 1"},
        ],
        "resume": "Une zone d'ombre.",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.questions_generator import generate_questions

    summary = {
        "project_overview": {
            "title": "Construction école",
            "buyer": "Mairie de Paris",
            "scope": "Gros oeuvre",
            "location": "Paris 15e",
            "deadline_submission": "2025-04-15",
            "estimated_budget": "2 000 000 EUR",
        },
        "key_points": [
            {"label": "Lots", "value": "Lot unique"},
        ],
        "risks": [
            {"risk": "Délai serré", "severity": "haut"},
        ],
    }

    result = generate_questions("Contexte.", summary_payload=summary, project_id="test")

    assert len(result["questions"]) == 1
    # Verify that the LLM was called with summary information in the prompt
    call_args = mock_llm.complete_json_with_thinking.call_args
    user_prompt = call_args.kwargs.get("user_prompt", call_args[1].get("user_prompt", ""))
    assert "Construction école" in user_prompt or "Mairie de Paris" in user_prompt


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_empty_summary(mock_llm):
    """Test question generation with empty summary."""
    mock_llm.complete_json_with_thinking.return_value = {
        "questions": [],
        "resume": "Aucune zone d'ombre majeure.",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.questions_generator import generate_questions

    result = generate_questions("Contexte.", summary_payload={})

    assert result["questions"] == []
    assert result["question_count"] == 0


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_text_truncation(mock_llm):
    """Test that long context is truncated."""
    mock_llm.complete_json_with_thinking.return_value = {
        "questions": [],
        "resume": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.questions_generator import generate_questions

    result = generate_questions("C" * 60_000)
    assert isinstance(result, dict)
    mock_llm.complete_json_with_thinking.assert_called_once()


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_llm_value_error(mock_llm):
    """Test ValueError propagation."""
    mock_llm.complete_json_with_thinking.side_effect = ValueError("Parse error")

    from app.services.questions_generator import generate_questions

    with pytest.raises(ValueError):
        generate_questions("Contexte.")


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_llm_runtime_error(mock_llm):
    """Test unexpected error propagation."""
    mock_llm.complete_json_with_thinking.side_effect = RuntimeError("API down")

    from app.services.questions_generator import generate_questions

    with pytest.raises(RuntimeError):
        generate_questions("Contexte.")


@patch("app.services.questions_generator.llm_service")
def test_generate_questions_no_project_id(mock_llm):
    """Test without project_id."""
    mock_llm.complete_json_with_thinking.return_value = {
        "questions": [
            {"question": "Q", "context": "", "priority": "HAUTE", "related_doc": "", "related_article": ""},
        ],
        "resume": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.questions_generator import generate_questions

    result = generate_questions("Contexte.")
    assert result["question_count"] == 1
