"""Tests for CCTP (Cahier des Clauses Techniques Particulières) analyzer — mock LLM."""
import pytest
from unittest.mock import patch


SAMPLE_CCTP_TEXT = """
CCTP - Cahier des Clauses Techniques Particulières

Lot 1 - Gros Oeuvre

Article 3.1 - Béton
Le béton utilisé sera de classe C30/37 XF3, conforme à la norme NF EN 206+A2.
Les essais de résistance seront réalisés tous les 50 m3 par un laboratoire agréé COFRAC.

Article 3.2 - Acier
Acier de construction S355 conforme à la norme NF EN 10025.
Certification AFNOR obligatoire.

Article 4.1 - Isolation
Isolation thermique par l'extérieur (ITE) en polystyrène expansé 140mm.
Performance minimale R = 4.5 m².K/W conforme RE 2020.
Marque Weber uniquement (pas d'équivalent autorisé).

Article 5.1 - Documents d'exécution
Le titulaire fournira :
- DOE complet dans les 30 jours suivant la réception
- DIUO
- Notes de calcul structures (Eurocodes)
- Plan d'Assurance Qualité (PAQ) avant démarrage

Article 6.1 - Risques
Diagnostic amiante avant travaux requis.
Étude géotechnique G2 AVP disponible en annexe.
""" + "A" * 200  # Ensure > 100 chars

MOCK_CCTP_RESPONSE = {
    "exigences_techniques": [
        {
            "category": "materiaux",
            "description": "Béton C30/37 XF3 conforme NF EN 206",
            "norme_ref": "NF EN 206+A2",
            "risk_level": "INFO",
            "citation": "béton de classe C30/37 XF3",
            "conseil": "Vérifier la disponibilité du béton XF3 auprès des centrales locales",
        },
        {
            "category": "restrictives",
            "description": "Marque Weber imposée sans équivalent",
            "norme_ref": None,
            "risk_level": "HAUT",
            "citation": "Marque Weber uniquement (pas d'équivalent autorisé)",
            "conseil": "Signaler le risque anticoncurrentiel (art. R2111-7 CCP)",
        },
    ],
    "normes_dtu_applicables": [
        {"code": "NF EN 206+A2", "titre": "Béton — Spécification", "applicabilite": "Gros oeuvre"},
        {"code": "NF EN 10025", "titre": "Acier de construction", "applicabilite": "Charpente métallique"},
    ],
    "materiaux_imposes": [
        {"designation": "Weber ITE", "marque_imposee": True, "anticoncurrentiel": True, "alternative": None},
    ],
    "essais_controles": [
        {"type": "Résistance béton", "frequence": "tous les 50 m3", "responsable": "labo_externe"},
    ],
    "documents_execution": [
        {"type": "DOE", "obligatoire": True, "delai": "30 jours après réception"},
        {"type": "DIUO", "obligatoire": True, "delai": ""},
        {"type": "notes_calcul", "obligatoire": True, "delai": ""},
        {"type": "PAQ", "obligatoire": True, "delai": "avant démarrage"},
    ],
    "risques_techniques": [
        {"type": "amiante", "severity": "HAUT", "description": "Diagnostic amiante requis", "mitigation": "Plan de retrait si présence confirmée"},
        {"type": "geotechnique", "severity": "MOYEN", "description": "Étude G2 AVP disponible", "mitigation": "Vérifier les préconisations de fondation"},
    ],
    "contradictions_techniques": [],
    "score_complexite_technique": 65,
    "resume": "Chantier de complexité haute avec exigences RE 2020, risque amiante et matériau anticoncurrentiel.",
    "confidence_overall": 0.85,
}


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_basic(mock_llm):
    """Test basic CCTP analysis with valid LLM response."""
    mock_llm.complete_json.return_value = MOCK_CCTP_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp(SAMPLE_CCTP_TEXT, project_id="test-cctp")

    assert isinstance(result, dict)
    assert len(result["exigences_techniques"]) == 2
    assert len(result["normes_dtu_applicables"]) == 2
    assert len(result["materiaux_imposes"]) == 1
    assert result["nb_anticoncurrentiel"] == 1
    assert len(result["essais_controles"]) == 1
    assert len(result["documents_execution"]) == 4
    assert len(result["risques_techniques"]) == 2
    assert result["score_complexite_technique"] == 65
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_short_text_returns_empty(mock_llm):
    """Test that text shorter than 100 chars returns empty result."""
    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("Too short", project_id="test")

    assert result["exigences_techniques"] == []
    assert result["score_complexite_technique"] == 0
    assert result["model_used"] == "none"
    # LLM should NOT have been called
    mock_llm.complete_json.assert_not_called()


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_empty_text(mock_llm):
    """Test with empty text."""
    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("", project_id="test")
    assert result["nb_exigences"] == 0
    mock_llm.complete_json.assert_not_called()


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_category_normalization(mock_llm):
    """Test that invalid categories are normalized to 'autre'."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [
            {"category": "INVALID_CAT", "description": "test", "risk_level": "INFO", "citation": "", "conseil": ""},
            {"category": "materiaux", "description": "ok", "risk_level": "BAS", "citation": "", "conseil": ""},
        ],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [],
        "documents_execution": [],
        "risques_techniques": [],
        "contradictions_techniques": [],
        "score_complexite_technique": 30,
        "resume": "",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("A" * 200)
    assert result["exigences_techniques"][0]["category"] == "autre"
    assert result["exigences_techniques"][1]["category"] == "materiaux"


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_risk_level_normalization(mock_llm):
    """Test that invalid risk levels are normalized."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [
            {"category": "normes", "description": "test", "risk_level": "EXTREME", "citation": "", "conseil": ""},
        ],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [],
        "documents_execution": [],
        "risques_techniques": [
            {"type": "amiante", "severity": "SUPER_HIGH", "description": "", "mitigation": ""},
        ],
        "contradictions_techniques": [],
        "score_complexite_technique": 40,
        "resume": "",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("A" * 200)
    assert result["exigences_techniques"][0]["risk_level"] == "INFO"
    assert result["risques_techniques"][0]["severity"] == "MOYEN"


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_score_clamped(mock_llm):
    """Test that complexity score is clamped to [0, 100]."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [],
        "documents_execution": [],
        "risques_techniques": [],
        "contradictions_techniques": [],
        "score_complexite_technique": 200,
        "resume": "",
        "confidence_overall": 2.0,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("A" * 200)
    assert result["score_complexite_technique"] == 100
    assert result["confidence_overall"] == 1.0


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_responsable_normalization(mock_llm):
    """Test that invalid responsable values are normalized to 'titulaire'."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [
            {"type": "Test béton", "frequence": "1/lot", "responsable": "unknown_resp"},
        ],
        "documents_execution": [
            {"type": "UNKNOWN_DOC", "obligatoire": True, "delai": ""},
        ],
        "risques_techniques": [
            {"type": "unknown_type", "severity": "MOYEN", "description": "", "mitigation": ""},
        ],
        "contradictions_techniques": [
            {"article_a": "A", "article_b": "B", "description": "test", "severity": "unknown_sev"},
        ],
        "score_complexite_technique": 50,
        "resume": "",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("A" * 200)
    assert result["essais_controles"][0]["responsable"] == "titulaire"
    assert result["documents_execution"][0]["type"] == "autre"
    assert result["risques_techniques"][0]["type"] == "autre"
    assert result["contradictions_techniques"][0]["severity"] == "medium"


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_counters(mock_llm):
    """Test that statistical counters are correct."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [
            {"category": "normes", "description": "t", "risk_level": "INFO", "citation": "", "conseil": ""},
            {"category": "materiaux", "description": "t", "risk_level": "BAS", "citation": "", "conseil": ""},
        ],
        "normes_dtu_applicables": [{"code": "DTU 13.1", "titre": "Fondations", "applicabilite": "GO"}],
        "materiaux_imposes": [
            {"designation": "X", "marque_imposee": True, "anticoncurrentiel": True, "alternative": None},
            {"designation": "Y", "marque_imposee": False, "anticoncurrentiel": False, "alternative": "ou equiv."},
        ],
        "essais_controles": [{"type": "A", "frequence": "", "responsable": "titulaire"}],
        "documents_execution": [{"type": "DOE", "obligatoire": True, "delai": ""}],
        "risques_techniques": [
            {"type": "amiante", "severity": "CRITIQUE", "description": "", "mitigation": ""},
            {"type": "plomb", "severity": "HAUT", "description": "", "mitigation": ""},
        ],
        "contradictions_techniques": [
            {"article_a": "A", "article_b": "B", "description": "", "severity": "high"},
        ],
        "score_complexite_technique": 70,
        "resume": "",
        "confidence_overall": 0.8,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("A" * 200)
    assert result["nb_exigences"] == 2
    assert result["nb_normes"] == 1
    assert result["nb_materiaux_imposes"] == 2
    assert result["nb_anticoncurrentiel"] == 1
    assert result["nb_essais"] == 1
    assert result["nb_documents_requis"] == 1
    assert result["nb_risques_techniques"] == 2
    assert result["nb_risques_critiques"] == 1
    assert result["nb_risques_hauts"] == 1
    assert result["nb_contradictions"] == 1
    assert result["nb_contradictions_high"] == 1


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_llm_value_error(mock_llm):
    """Test ValueError propagation."""
    mock_llm.complete_json.side_effect = ValueError("Bad JSON")

    from app.services.cctp_analyzer import analyze_cctp

    with pytest.raises(ValueError):
        analyze_cctp("A" * 200)


@patch("app.services.cctp_analyzer.llm_service")
def test_analyze_cctp_text_truncation(mock_llm):
    """Test that long text is truncated."""
    mock_llm.complete_json.return_value = {
        "exigences_techniques": [],
        "normes_dtu_applicables": [],
        "materiaux_imposes": [],
        "essais_controles": [],
        "documents_execution": [],
        "risques_techniques": [],
        "contradictions_techniques": [],
        "score_complexite_technique": 0,
        "resume": "",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.cctp_analyzer import analyze_cctp

    result = analyze_cctp("B" * 60_000)
    assert isinstance(result, dict)
    mock_llm.complete_json.assert_called_once()
