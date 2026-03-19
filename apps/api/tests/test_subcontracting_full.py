"""Tests for subcontracting analyzer — mock LLM + DB."""
import pytest
from unittest.mock import patch, MagicMock


MOCK_SUBCONTRACTING_RESPONSE = {
    "sous_traitance_autorisee": True,
    "restrictions_rc": "Sous-traitance limitée à 30% du montant total",
    "lots_analysis": [
        {
            "lot": "Lot 1 - Gros oeuvre",
            "competence_requise": "Béton armé, fondations profondes",
            "competence_interne": True,
            "sous_traitance_recommandee": False,
            "justification": "Compétence interne confirmée",
            "risque": "faible",
        },
        {
            "lot": "Lot 2 - Électricité",
            "competence_requise": "Courants forts/faibles, certification Qualifelec",
            "competence_interne": False,
            "sous_traitance_recommandee": True,
            "justification": "Certification Qualifelec non détenue",
            "risque": "modéré",
        },
    ],
    "conflits": [],
    "paiement_direct_applicable": True,
    "seuil_paiement_direct_eur": 600,
    "recommandations": [
        "Sous-traiter le lot électricité à un partenaire Qualifelec",
        "Vérifier la compatibilité avec la limite de 30% du RC",
    ],
    "score_risque": 35,
    "resume": "Un lot nécessite sous-traitance (électricité). Risque global modéré.",
    "confidence_overall": 0.75,
}


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_basic(mock_retrieve, mock_format, mock_llm):
    """Test basic subcontracting analysis with mocked DB and LLM."""
    # Setup mocks
    mock_retrieve.return_value = [{"text": "sous-traitance autorisée dans la limite de 30%"}]
    mock_format.return_value = "sous-traitance autorisée dans la limite de 30%"
    mock_llm.complete_json.return_value = MOCK_SUBCONTRACTING_RESPONSE

    # Mock DB session and models
    mock_db = MagicMock()

    # Mock project
    mock_project = MagicMock()
    mock_project.id = "proj-123"
    mock_project.org_id = "org-456"

    # Mock company profile
    mock_profile = MagicMock()
    mock_profile.specialties = ["Gros oeuvre", "VRD"]
    mock_profile.certifications = ["Qualibat 1312"]
    mock_profile.employee_count = 50
    mock_profile.revenue_eur = 5000000
    mock_profile.partenaires_specialites = ["Électricité", "Plomberie"]

    # Setup query chain
    mock_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_project,  # first call: AoProject
        mock_profile,  # second call: CompanyProfile
    ]

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("proj-123", mock_db)

    assert result["sous_traitance_autorisee"] is True
    assert len(result["lots_analysis"]) == 2
    assert result["score_risque"] == 35
    assert result["confidence_overall"] == 0.75
    mock_llm.complete_json.assert_called_once()


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_project_not_found(mock_retrieve, mock_format, mock_llm):
    """Test when project is not found in DB."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("nonexistent", mock_db)

    assert result == {"error": "Projet introuvable"}
    mock_llm.complete_json.assert_not_called()


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_no_profile(mock_retrieve, mock_format, mock_llm):
    """Test when company profile does not exist."""
    mock_retrieve.return_value = []
    mock_format.return_value = ""
    mock_llm.complete_json.return_value = MOCK_SUBCONTRACTING_RESPONSE

    mock_db = MagicMock()

    mock_project = MagicMock()
    mock_project.org_id = "org-789"

    mock_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_project,  # AoProject found
        None,          # CompanyProfile not found
    ]

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("proj-123", mock_db)

    # Should still work with "Aucun profil entreprise renseigné"
    assert isinstance(result, dict)
    mock_llm.complete_json.assert_called_once()
    call_kwargs = mock_llm.complete_json.call_args
    system_prompt = call_kwargs.kwargs.get("system_prompt", call_kwargs[1].get("system_prompt", call_kwargs[0][0] if call_kwargs[0] else ""))
    assert "Aucun profil" in system_prompt


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_llm_returns_none(mock_retrieve, mock_format, mock_llm):
    """Test when LLM returns empty/falsy result."""
    mock_retrieve.return_value = []
    mock_format.return_value = ""
    mock_llm.complete_json.return_value = {}  # falsy

    mock_db = MagicMock()
    mock_project = MagicMock()
    mock_project.org_id = "org-1"
    mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_project, None]

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("proj-1", mock_db)

    assert result["sous_traitance_autorisee"] is None
    assert result["lots_analysis"] == []
    assert result["score_risque"] == 0
    assert result["confidence_overall"] == 0.0


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_score_clamped(mock_retrieve, mock_format, mock_llm):
    """Test that score_risque is clamped to [0, 100]."""
    mock_retrieve.return_value = []
    mock_format.return_value = ""
    mock_llm.complete_json.return_value = {
        "sous_traitance_autorisee": True,
        "score_risque": 200,
        "confidence_overall": 5.0,
        "lots_analysis": [],
        "conflits": [],
        "recommandations": [],
        "resume": "",
    }

    mock_db = MagicMock()
    mock_project = MagicMock()
    mock_project.org_id = "org-1"
    mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_project, None]

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("proj-1", mock_db)

    assert result["score_risque"] == 100
    assert result["confidence_overall"] == 1.0


@patch("app.services.subcontracting_analyzer.llm_service")
@patch("app.services.subcontracting_analyzer.format_context")
@patch("app.services.subcontracting_analyzer.retrieve_relevant_chunks")
def test_analyze_subcontracting_no_chunks(mock_retrieve, mock_format, mock_llm):
    """Test when no relevant chunks are found in DB."""
    mock_retrieve.return_value = []
    mock_llm.complete_json.return_value = MOCK_SUBCONTRACTING_RESPONSE

    mock_db = MagicMock()
    mock_project = MagicMock()
    mock_project.org_id = "org-1"
    mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_project, None]

    from app.services.subcontracting_analyzer import analyze_subcontracting

    result = analyze_subcontracting("proj-1", mock_db)

    assert isinstance(result, dict)
    # format_context should not have been called since chunks are empty
    mock_format.assert_not_called()
