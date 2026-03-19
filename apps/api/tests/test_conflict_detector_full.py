"""Tests for conflict detector — mock LLM."""
import pytest
from unittest.mock import patch


MOCK_CONFLICT_RESPONSE = {
    "conflicts": [
        {
            "conflict_type": "delai",
            "severity": "HAUT",
            "doc_a": "RC",
            "doc_b": "CCAP",
            "description": "Le RC annonce un délai d'exécution de 6 mois mais le CCAP mentionne 180 jours ouvrés.",
            "citation_a": "délai d'exécution : 6 mois",
            "citation_b": "durée des travaux : 180 jours ouvrés",
            "recommendation": "Demander clarification sur la base calendaire du délai.",
        },
        {
            "conflict_type": "exigence",
            "severity": "CRITIQUE",
            "doc_a": "RC",
            "doc_b": "AE",
            "description": "Le RC autorise les variantes mais l'AE les interdit.",
            "citation_a": "variantes autorisées",
            "citation_b": "les variantes ne sont pas autorisées",
            "recommendation": "Poser la question à l'acheteur avant soumission.",
        },
        {
            "conflict_type": "montant",
            "severity": "MOYEN",
            "doc_a": "CCTP",
            "doc_b": "DPGF",
            "description": "Quantité de peinture différente entre CCTP et DPGF.",
            "citation_a": "200 m² de peinture",
            "citation_b": "150 m² de peinture",
            "recommendation": "Retenir la quantité du CCTP (document technique de référence).",
        },
    ],
    "nb_critiques": 1,
    "nb_total": 3,
    "resume": "3 conflits détectés dont 1 critique sur les variantes.",
    "confidence_overall": 0.9,
}


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_basic(mock_llm):
    """Test basic conflict detection with multiple documents."""
    mock_llm.complete_json_with_thinking.return_value = MOCK_CONFLICT_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.conflict_detector import detect_conflicts

    texts = {
        "RC": "Règlement de consultation. Délai 6 mois. Variantes autorisées.",
        "CCAP": "Cahier clauses admin. Durée 180 jours ouvrés.",
        "CCTP": "Cahier clauses techniques. 200 m² peinture.",
    }
    result = detect_conflicts(texts, project_id="test-conf")

    assert isinstance(result, dict)
    assert len(result["conflicts"]) == 3
    assert result["nb_critiques"] == 1
    assert result["nb_total"] == 3
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"
    assert result["documents_analyzed"] == ["RC", "CCAP", "CCTP"]


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_sorted_by_severity(mock_llm):
    """Test that conflicts are sorted by severity descending."""
    mock_llm.complete_json_with_thinking.return_value = MOCK_CONFLICT_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({"RC": "text1", "CCAP": "text2"})

    severities = [c["severity"] for c in result["conflicts"]]
    severity_order = {"CRITIQUE": 0, "HAUT": 1, "MOYEN": 2, "BAS": 3}
    assert severities == sorted(severities, key=lambda s: severity_order[s])


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_empty_texts(mock_llm):
    """Test with no documents provided."""
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({})

    assert result["conflicts"] == []
    assert result["nb_total"] == 0
    assert result["documents_analyzed"] == []
    mock_llm.complete_json_with_thinking.assert_not_called()


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_single_document(mock_llm):
    """Test with only one document — requires at least 2."""
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({"RC": "Texte du RC seul"})

    assert result["conflicts"] == []
    assert result["nb_total"] == 0
    assert "au moins 2 documents" in result["resume"]
    mock_llm.complete_json_with_thinking.assert_not_called()


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_no_conflicts_found(mock_llm):
    """Test when LLM finds no conflicts."""
    mock_llm.complete_json_with_thinking.return_value = {
        "conflicts": [],
        "nb_critiques": 0,
        "nb_total": 0,
        "resume": "Aucun conflit détecté entre les documents.",
        "confidence_overall": 0.95,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({"RC": "text1", "CCAP": "text2"})

    assert result["conflicts"] == []
    assert result["nb_critiques"] == 0
    assert result["nb_total"] == 0


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_counter_correction(mock_llm):
    """Test that counters are recalculated from actual conflicts list."""
    mock_llm.complete_json_with_thinking.return_value = {
        "conflicts": [
            {"conflict_type": "delai", "severity": "CRITIQUE", "doc_a": "A", "doc_b": "B",
             "description": "", "citation_a": "", "citation_b": "", "recommendation": ""},
            {"conflict_type": "montant", "severity": "CRITIQUE", "doc_a": "A", "doc_b": "B",
             "description": "", "citation_a": "", "citation_b": "", "recommendation": ""},
        ],
        "nb_critiques": 999,  # intentionally wrong
        "nb_total": 999,      # intentionally wrong
        "resume": "",
        "confidence_overall": 0.8,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({"RC": "x", "CCAP": "y"})
    assert result["nb_critiques"] == 2  # corrected
    assert result["nb_total"] == 2      # corrected


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_deviation_ccag_count(mock_llm):
    """Test that CCAG deviation count is computed."""
    mock_llm.complete_json_with_thinking.return_value = {
        "conflicts": [
            {"conflict_type": "deviation_ccag", "severity": "HAUT", "doc_a": "CCAG", "doc_b": "CCAP",
             "description": "", "citation_a": "", "citation_b": "", "recommendation": ""},
            {"conflict_type": "deviation_ccag", "severity": "MOYEN", "doc_a": "CCAG", "doc_b": "CCAP",
             "description": "", "citation_a": "", "citation_b": "", "recommendation": ""},
            {"conflict_type": "delai", "severity": "BAS", "doc_a": "RC", "doc_b": "CCAP",
             "description": "", "citation_a": "", "citation_b": "", "recommendation": ""},
        ],
        "nb_critiques": 0,
        "nb_total": 3,
        "resume": "",
        "confidence_overall": 0.7,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.conflict_detector import detect_conflicts

    result = detect_conflicts({"RC": "x", "CCAP": "y"})
    assert result["nb_deviation_ccag"] == 2


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_llm_value_error(mock_llm):
    """Test ValueError propagation."""
    mock_llm.complete_json_with_thinking.side_effect = ValueError("Bad JSON")

    from app.services.conflict_detector import detect_conflicts

    with pytest.raises(ValueError):
        detect_conflicts({"RC": "x", "CCAP": "y"})


@patch("app.services.conflict_detector.llm_service")
def test_detect_conflicts_llm_runtime_error(mock_llm):
    """Test unexpected error propagation."""
    mock_llm.complete_json_with_thinking.side_effect = RuntimeError("API down")

    from app.services.conflict_detector import detect_conflicts

    with pytest.raises(RuntimeError):
        detect_conflicts({"RC": "x", "CCAP": "y"})


def test_build_documents_block():
    """Test the internal document block builder."""
    from app.services.conflict_detector import _build_documents_block

    texts = {"RC": "contenu RC", "CCAP": "contenu CCAP"}
    block = _build_documents_block(texts, max_chars_per_doc=1000)

    assert "DOCUMENT : RC" in block
    assert "DOCUMENT : CCAP" in block
    assert "contenu RC" in block
    assert "contenu CCAP" in block


def test_build_documents_block_truncation():
    """Test that document block truncates long texts."""
    from app.services.conflict_detector import _build_documents_block

    texts = {"RC": "A" * 5000}
    block = _build_documents_block(texts, max_chars_per_doc=100)

    assert "[... texte tronqué ...]" in block
