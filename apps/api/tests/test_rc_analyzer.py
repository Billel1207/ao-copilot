"""Tests for RC (Règlement de Consultation) analyzer — mock LLM."""
import pytest
from unittest.mock import patch


SAMPLE_RC_TEXT = """
Règlement de Consultation - Marché de travaux

Article 1 - Objet du marché
Construction d'un groupe scolaire - Commune de Villepinte

Article 2 - Conditions de participation
Les candidats doivent justifier d'un chiffre d'affaires annuel minimum de 2 000 000 EUR HT.
Certification Qualibat 1312 requise. Références similaires des 3 dernières années.

Article 3 - Groupement
Le groupement est autorisé sous forme solidaire.
Le mandataire doit être solidaire.

Article 4 - Variantes
Les variantes ne sont pas autorisées.

Article 5 - Visite de site
Une visite de site est obligatoire le 15 mars 2025 à 10h.

Article 6 - Allotissement
Lot unique.

Article 7 - Procédure
Appel d'offres ouvert selon les articles L2124-1 et suivants du CCP.
"""

MOCK_RC_RESPONSE = {
    "who_can_apply": [
        {
            "condition": "Chiffre d'affaires annuel minimum de 2 000 000 EUR HT",
            "type": "hard",
            "details": "Justificatif des 3 derniers exercices",
            "citations": [{"doc": "RC", "page": 1, "quote": "CA annuel minimum de 2 000 000 EUR HT"}],
        },
        {
            "condition": "Certification Qualibat 1312",
            "type": "hard",
            "details": "Certification en cours de validité",
            "citations": [],
        },
    ],
    "groupement": {
        "groupement_autorise": True,
        "forme_imposee": "solidaire",
        "mandataire_solidaire": True,
        "details": "Groupement solidaire imposé",
    },
    "sous_traitance": {
        "sous_traitance_autorisee": True,
        "restrictions": [],
        "details": "",
    },
    "variantes_autorisees": False,
    "variantes_details": "Les variantes ne sont pas autorisées",
    "prestations_supplementaires": False,
    "prestations_details": "",
    "visite_site_obligatoire": True,
    "visite_details": "15 mars 2025 à 10h",
    "langue_offre": "français",
    "devise_offre": "EUR",
    "duree_validite_offres_jours": 120,
    "nombre_lots": 1,
    "lots_details": [
        {"numero": 1, "intitule": "Lot unique", "description": "Construction groupe scolaire", "montant_estime": None},
    ],
    "procedure_type": "Appel d'offres ouvert",
    "resume": "Marché de travaux en lot unique pour un groupe scolaire. Groupement solidaire autorisé. Visite de site obligatoire.",
    "confidence_overall": 0.85,
}


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_basic(mock_llm):
    """Test basic RC analysis with valid LLM response."""
    mock_llm.complete_json.return_value = MOCK_RC_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc(SAMPLE_RC_TEXT, project_id="test-rc")

    assert isinstance(result, dict)
    assert len(result["who_can_apply"]) == 2
    assert result["who_can_apply"][0]["type"] == "hard"
    assert result["groupement"]["groupement_autorise"] is True
    assert result["groupement"]["forme_imposee"] == "solidaire"
    assert result["variantes_autorisees"] is False
    assert result["visite_site_obligatoire"] is True
    assert result["nombre_lots"] == 1
    assert result["procedure_type"] == "Appel d'offres ouvert"
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"
    assert result["confidence_overall"] == 0.85


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_empty_conditions(mock_llm):
    """Test RC analysis with no access conditions."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [],
        "groupement": {},
        "sous_traitance": {},
        "variantes_autorisees": False,
        "procedure_type": "MAPA",
        "resume": "Procédure adaptée sans conditions spécifiques.",
        "confidence_overall": 0.6,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("RC simple sans conditions.")

    assert result["who_can_apply"] == []
    assert result["groupement"]["groupement_autorise"] is True  # default
    assert result["procedure_type"] == "MAPA"


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_invalid_condition_type(mock_llm):
    """Test that invalid condition type is normalized to 'hard'."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [
            {"condition": "Test", "type": "invalid_type", "details": "", "citations": []},
        ],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("Texte RC.")
    assert result["who_can_apply"][0]["type"] == "hard"


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_lots_count_reconciled(mock_llm):
    """Test that nombre_lots is reconciled from lots_details when None."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "nombre_lots": None,
        "lots_details": [
            {"numero": 1, "intitule": "Lot 1", "description": "Gros oeuvre"},
            {"numero": 2, "intitule": "Lot 2", "description": "Second oeuvre"},
        ],
        "confidence_overall": 0.7,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("Texte RC multi-lots.")
    assert result["nombre_lots"] == 2


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_confidence_clamped(mock_llm):
    """Test that confidence is clamped to [0, 1]."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "confidence_overall": 1.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("Texte.")
    assert result["confidence_overall"] == 1.0


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_llm_value_error(mock_llm):
    """Test that ValueError from LLM is re-raised."""
    mock_llm.complete_json.side_effect = ValueError("Missing required keys")

    from app.services.rc_analyzer import analyze_rc

    with pytest.raises(ValueError, match="Missing required keys"):
        analyze_rc("Texte RC.")


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_llm_unexpected_error(mock_llm):
    """Test that unexpected exceptions from LLM are re-raised."""
    mock_llm.complete_json.side_effect = ConnectionError("Network error")

    from app.services.rc_analyzer import analyze_rc

    with pytest.raises(ConnectionError):
        analyze_rc("Texte RC.")


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_text_truncation(mock_llm):
    """Test that long text is truncated."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    long_text = "B" * 60_000
    result = analyze_rc(long_text)
    assert isinstance(result, dict)
    mock_llm.complete_json.assert_called_once()


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_non_dict_condition_filtered(mock_llm):
    """Test that non-dict entries in who_can_apply are filtered out."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": ["not_a_dict", {"condition": "OK", "type": "soft", "details": "", "citations": []}],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("Texte.")
    assert len(result["who_can_apply"]) == 1


@patch("app.services.rc_analyzer.llm_service")
def test_analyze_rc_duree_validite_clamped(mock_llm):
    """Test that duree_validite_offres_jours is clamped to minimum 1."""
    mock_llm.complete_json.return_value = {
        "who_can_apply": [],
        "groupement": {},
        "sous_traitance": {},
        "procedure_type": "AOO",
        "duree_validite_offres_jours": -5,
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.rc_analyzer import analyze_rc

    result = analyze_rc("Texte.")
    assert result["duree_validite_offres_jours"] == 1
