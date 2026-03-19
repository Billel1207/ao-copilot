"""Tests for AE (Acte d'Engagement) analyzer — mock LLM."""
import pytest
from unittest.mock import patch


SAMPLE_AE_TEXT = """
Acte d'Engagement

Article 1 - Prix
Le prix du marché est forfaitaire et ferme.
Montant total HT : 1 250 000 EUR.

Article 2 - Révision de prix
Aucune clause de révision de prix n'est prévue.

Article 3 - Durée
Durée du marché : 12 mois à compter de la notification.

Article 4 - Pénalités
Pénalités de retard : 1/1000 du montant HT par jour calendaire.
Plafond des pénalités : 10% du montant HT.

Article 5 - Retenue de garantie
Retenue de garantie : 5% du montant des travaux.

Article 6 - Avance
Avance forfaitaire : 5% du montant HT.

Article 7 - Paiement
Délai de paiement : 30 jours.
"""

MOCK_AE_RESPONSE = {
    "prix_forme": "forfaitaire",
    "prix_revision": False,
    "prix_revision_details": "Aucune clause de révision prévue",
    "montant_total_ht": "1 250 000 EUR",
    "duree_marche": "12 mois",
    "reconduction": False,
    "reconduction_details": "",
    "penalites_retard": "1/1000 par jour, plafond 10%",
    "retenue_garantie_pct": 5.0,
    "avance_pct": 5.0,
    "delai_paiement_jours": 30,
    "clauses_risquees": [
        {
            "clause_type": "Révision de prix",
            "description": "Absence de clause de révision sur un marché de 12 mois",
            "risk_level": "HAUT",
            "citation": "Aucune clause de révision de prix n'est prévue",
            "conseil": "Demander l'insertion d'une clause de révision indexée sur les indices BT",
        }
    ],
    "ccag_derogations": [],
    "score_risque_global": 45,
    "resume": "Marché forfaitaire de 1,25M EUR sur 12 mois sans révision de prix.",
    "confidence_overall": 0.9,
}


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_basic(mock_llm):
    """Test basic AE analysis with valid LLM response."""
    mock_llm.complete_json.return_value = MOCK_AE_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae(SAMPLE_AE_TEXT, project_id="test-ae")

    assert result["prix_forme"] == "forfaitaire"
    assert result["prix_revision"] is False
    assert result["montant_total_ht"] == "1 250 000 EUR"
    assert result["duree_marche"] == "12 mois"
    assert result["retenue_garantie_pct"] == 5.0
    assert result["avance_pct"] == 5.0
    assert result["delai_paiement_jours"] == 30
    assert result["score_risque_global"] == 45
    assert len(result["clauses_risquees"]) == 1
    assert result["clauses_risquees"][0]["risk_level"] == "HAUT"
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_no_clauses(mock_llm):
    """Test AE analysis with no risky clauses."""
    mock_llm.complete_json.return_value = {
        "prix_forme": "unitaire",
        "prix_revision": True,
        "prix_revision_details": "Indice BT01",
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 10,
        "resume": "Conditions équilibrées.",
        "confidence_overall": 0.8,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("AE simple.")
    assert result["clauses_risquees"] == []
    assert result["nb_clauses_critiques"] == 0
    assert result["nb_clauses_hautes"] == 0


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_score_clamped(mock_llm):
    """Test that score is clamped between 0 and 100."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": -10,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("Texte.")
    assert result["score_risque_global"] == 0


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_retenue_garantie_clamped(mock_llm):
    """Test that retenue_garantie_pct is clamped to [0, 100]."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 20,
        "retenue_garantie_pct": 150.0,
        "avance_pct": -5.0,
        "delai_paiement_jours": -1,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("Texte.")
    assert result["retenue_garantie_pct"] == 100.0
    assert result["avance_pct"] == 0.0
    assert result["delai_paiement_jours"] == 0


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_invalid_risk_level_normalized(mock_llm):
    """Test that invalid risk_level is normalized to MOYEN."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [
            {"clause_type": "Test", "description": "", "risk_level": "EXTREME", "citation": "", "conseil": ""},
        ],
        "ccag_derogations": [],
        "score_risque_global": 50,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("Texte.")
    assert result["clauses_risquees"][0]["risk_level"] == "MOYEN"


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_derogation_impact_validated(mock_llm):
    """Test that derogation impact is validated."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [
            {"article_ccag": "14.1", "valeur_ccag": "5%", "valeur_ae": "0%", "impact": "BAD", "description": "test"},
        ],
        "score_risque_global": 30,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("Texte.")
    assert result["ccag_derogations"][0]["impact"] == "NEUTRE"


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_missing_fields_defaults(mock_llm):
    """Test that missing optional fields get defaults."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 0,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("Texte.")
    assert result["prix_forme"] == ""
    assert result["prix_revision"] is False
    assert result["reconduction"] is False
    assert result["montant_total_ht"] is None
    assert result["retenue_garantie_pct"] is None
    assert result["avance_pct"] is None


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_llm_value_error(mock_llm):
    """Test ValueError propagation."""
    mock_llm.complete_json.side_effect = ValueError("Bad JSON")

    from app.services.ae_analyzer import analyze_ae

    with pytest.raises(ValueError):
        analyze_ae("Texte.")


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_llm_runtime_error(mock_llm):
    """Test unexpected error propagation."""
    mock_llm.complete_json.side_effect = RuntimeError("Unexpected")

    from app.services.ae_analyzer import analyze_ae

    with pytest.raises(RuntimeError):
        analyze_ae("Texte.")


@patch("app.services.ae_analyzer.llm_service")
def test_analyze_ae_text_truncation(mock_llm):
    """Test long text truncation."""
    mock_llm.complete_json.return_value = {
        "clauses_risquees": [],
        "ccag_derogations": [],
        "score_risque_global": 0,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.ae_analyzer import analyze_ae

    result = analyze_ae("X" * 60_000)
    assert isinstance(result, dict)
