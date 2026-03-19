"""Tests for CCAP analyzer — mock LLM to avoid real API calls."""
import pytest
from unittest.mock import patch, MagicMock


SAMPLE_CCAP_TEXT = """
Article 7.3 - Pénalités de retard
Le titulaire est soumis à des pénalités de retard de 1/500 du montant HT du marché par jour calendaire.
Aucun plafond n'est prévu.

Article 8.1 - Retenue de garantie
La retenue de garantie est fixée à 5% du montant du marché.

Article 12 - Résiliation
Le pouvoir adjudicateur peut résilier le marché sans indemnité avec un préavis de 15 jours.

Article 14 - Sous-traitance
La sous-traitance est limitée à 30% du montant total du marché.
"""

MOCK_LLM_RESPONSE = {
    "clauses_risquees": [
        {
            "article_reference": "Article 7.3",
            "clause_text": "Pénalités de retard de 1/500 du montant HT par jour",
            "risk_level": "CRITIQUE",
            "risk_type": "Pénalités de retard",
            "conseil": "Négocier un taux de 1/3000 conforme au CCAG standard",
            "citation": "pénalités de retard de 1/500 du montant HT du marché",
        },
        {
            "article_reference": "Article 12",
            "clause_text": "Résiliation sans indemnité avec préavis de 15 jours",
            "risk_level": "HAUT",
            "risk_type": "Résiliation facilitée",
            "conseil": "Demander un préavis de 30 jours minimum avec indemnisation",
            "citation": "résilier le marché sans indemnité avec un préavis de 15 jours",
        },
    ],
    "ccag_derogations": [
        {
            "article_ccag": "19.1",
            "valeur_ccag": "1/3000 par jour",
            "valeur_ccap": "1/500 par jour",
            "impact": "DEFAVORABLE",
            "description": "Pénalités 6x plus sévères que le CCAG standard",
        },
    ],
    "score_risque_global": 72,
    "nb_clauses_critiques": 1,
    "resume_risques": "Le CCAP présente un risque élevé avec des pénalités excessives et une clause de résiliation défavorable.",
}


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_basic(mock_llm):
    """Test basic CCAP analysis with valid LLM response."""
    mock_llm.complete_json_with_thinking.return_value = MOCK_LLM_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks(SAMPLE_CCAP_TEXT, project_id="test-proj")

    assert isinstance(result, dict)
    assert "clauses_risquees" in result
    assert "ccag_derogations" in result
    assert "score_risque_global" in result
    assert "nb_clauses_critiques" in result
    assert "resume_risques" in result
    assert "model_used" in result

    assert len(result["clauses_risquees"]) == 2
    assert result["score_risque_global"] == 72
    assert result["nb_clauses_critiques"] == 1
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"

    mock_llm.complete_json_with_thinking.assert_called_once()


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_empty_clauses(mock_llm):
    """Test CCAP analysis when LLM returns no risky clauses."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 0,
        "nb_clauses_critiques": 0,
        "resume_risques": "Aucune clause risquée détectée.",
    }
    mock_llm.get_model_name.return_value = "anthropic:test-model"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Document CCAP simple sans risque.")

    assert result["clauses_risquees"] == []
    assert result["ccag_derogations"] == []
    assert result["score_risque_global"] == 0
    assert result["nb_clauses_critiques"] == 0


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_score_clamped(mock_llm):
    """Test that risk score is clamped between 0 and 100."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 150,  # over 100
        "nb_clauses_critiques": 0,
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Texte CCAP quelconque.")
    assert result["score_risque_global"] == 100


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_invalid_risk_level(mock_llm):
    """Test that invalid risk_level is normalized to MOYEN."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [
            {
                "article_reference": "Art. 5",
                "clause_text": "Clause test",
                "risk_level": "INVALIDE",
                "risk_type": "Test",
                "conseil": "",
                "citation": "",
            }
        ],
        "ccag_derogations": [],
        "score_risque_global": 30,
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Texte CCAP.")
    assert result["clauses_risquees"][0]["risk_level"] == "MOYEN"


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_derogation_validation(mock_llm):
    """Test that derogation impact values are validated."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [
            {
                "article_ccag": "14.3",
                "valeur_ccag": "5%",
                "valeur_ccap": "10%",
                "impact": "INVALID_IMPACT",
                "description": "test",
            }
        ],
        "score_risque_global": 20,
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Texte.")
    assert result["ccag_derogations"][0]["impact"] == "NEUTRE"


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_text_truncation(mock_llm):
    """Test that long text is truncated to max_chars."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 0,
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    long_text = "A" * 60_000
    result = analyze_ccap_risks(long_text)
    assert isinstance(result, dict)
    # Verify the LLM was called (text was truncated internally)
    mock_llm.complete_json_with_thinking.assert_called_once()


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_llm_value_error(mock_llm):
    """Test that ValueError from LLM is re-raised."""
    mock_llm.complete_json_with_thinking.side_effect = ValueError("LLM parse error")

    from app.services.ccap_analyzer import analyze_ccap_risks

    with pytest.raises(ValueError, match="LLM parse error"):
        analyze_ccap_risks("Texte CCAP.")


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_risks_llm_unexpected_error(mock_llm):
    """Test that unexpected exceptions from LLM are re-raised."""
    mock_llm.complete_json_with_thinking.side_effect = RuntimeError("API down")

    from app.services.ccap_analyzer import analyze_ccap_risks

    with pytest.raises(RuntimeError, match="API down"):
        analyze_ccap_risks("Texte CCAP.")


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_nb_critiques_auto_counted(mock_llm):
    """Test that nb_clauses_critiques is auto-counted when not provided by LLM."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [
            {"risk_level": "CRITIQUE", "article_reference": "A", "clause_text": "", "risk_type": "", "conseil": "", "citation": ""},
            {"risk_level": "CRITIQUE", "article_reference": "B", "clause_text": "", "risk_type": "", "conseil": "", "citation": ""},
            {"risk_level": "HAUT", "article_reference": "C", "clause_text": "", "risk_type": "", "conseil": "", "citation": ""},
        ],
        "ccag_derogations": [],
        "score_risque_global": 80,
        # nb_clauses_critiques intentionally omitted
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Texte.")
    assert result["nb_clauses_critiques"] == 2


@patch("app.services.ccap_analyzer.llm_service")
def test_analyze_ccap_non_dict_clause_filtered(mock_llm):
    """Test that non-dict entries in clauses_risquees are filtered out."""
    mock_llm.complete_json_with_thinking.return_value = {
        "clauses_risquees": [
            "not a dict",
            {"article_reference": "A", "clause_text": "ok", "risk_level": "BAS", "risk_type": "t", "conseil": "", "citation": ""},
        ],
        "ccag_derogations": ["also not a dict"],
        "score_risque_global": 10,
        "resume_risques": "",
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ccap_analyzer import analyze_ccap_risks

    result = analyze_ccap_risks("Texte.")
    assert len(result["clauses_risquees"]) == 1
    assert len(result["ccag_derogations"]) == 0
