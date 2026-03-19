"""Tests for DC checker (document compliance) — mock LLM."""
import pytest
from unittest.mock import patch


SAMPLE_DCE_TEXT = """
Article 5 - Pièces de candidature

Le candidat devra fournir les documents suivants :
- Formulaire DC1 (lettre de candidature) version 2024
- Formulaire DC2 (déclaration du candidat) version 2024
- Attestation de régularité fiscale (année en cours)
- Attestation URSSAF de moins de 6 mois
- Attestation d'assurance responsabilité civile professionnelle
- Attestation d'assurance décennale
- Extrait Kbis de moins de 3 mois
- Certification Qualibat 1312 en cours de validité
- Certification ISO 9001
- Références similaires des 3 dernières années
"""

MOCK_DC_RESPONSE = {
    "documents_requis": [
        {"document": "DC1 v2024", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "Version 2024", "citations": []},
        {"document": "DC2 v2024", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "Version 2024", "citations": []},
        {"document": "Attestation fiscale", "obligatoire": True, "date_validite": "2025-12-31", "statut": "À_FOURNIR", "details": "", "citations": []},
        {"document": "Attestation URSSAF", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "Moins de 6 mois", "citations": []},
        {"document": "Assurance RC Pro", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
        {"document": "Assurance décennale", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
        {"document": "Kbis", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "Moins de 3 mois", "citations": []},
        {"document": "Qualibat 1312", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
        {"document": "ISO 9001", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
    ],
    "formulaires_obligatoires": ["DC1 v2024", "DC2 v2024"],
    "attestations_fiscales": True,
    "attestation_urssaf": True,
    "attestation_assurance_rc": True,
    "attestation_assurance_decennale": True,
    "kbis_requis": True,
    "certifications_requises": ["Qualibat 1312"],
    "alertes": [],
    "resume": "9 documents requis dont DC1/DC2 v2024, attestations sociales et fiscales, assurances, Kbis et certifications.",
    "confidence_overall": 0.9,
}


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_requirements_basic(mock_llm):
    """Test basic DC requirements analysis."""
    mock_llm.complete_json.return_value = MOCK_DC_RESPONSE
    mock_llm.get_model_name.return_value = "anthropic:claude-sonnet-4-20250514"

    from app.services.dc_checker import analyze_dc_requirements

    result = analyze_dc_requirements(SAMPLE_DCE_TEXT, project_id="test-dc")

    assert isinstance(result, dict)
    assert len(result["documents_requis"]) == 9
    assert result["attestations_fiscales"] is True
    assert result["attestation_urssaf"] is True
    assert result["kbis_requis"] is True
    assert result["model_used"] == "anthropic:claude-sonnet-4-20250514"
    # Qualibat and ISO should be in certifications
    assert "Qualibat 1312" in result["certifications_requises"]


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_certification_enrichment(mock_llm):
    """Test that certifications are enriched from documents_requis."""
    mock_llm.complete_json.return_value = {
        "documents_requis": [
            {"document": "Qualibat 2111", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
            {"document": "ISO 14001", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
            {"document": "RGE", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "", "citations": []},
        ],
        "formulaires_obligatoires": [],
        "attestations_fiscales": False,
        "attestation_urssaf": False,
        "attestation_assurance_rc": False,
        "attestation_assurance_decennale": False,
        "kbis_requis": False,
        "certifications_requises": [],  # empty initially
        "alertes": [],
        "resume": "",
        "confidence_overall": 0.7,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.dc_checker import analyze_dc_requirements

    result = analyze_dc_requirements("Texte DCE avec certifications.")

    certs = result["certifications_requises"]
    assert "Qualibat 2111" in certs
    assert "ISO 14001" in certs
    assert "RGE" in certs


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_no_documents(mock_llm):
    """Test with no required documents."""
    mock_llm.complete_json.return_value = {
        "documents_requis": [],
        "formulaires_obligatoires": [],
        "attestations_fiscales": False,
        "attestation_urssaf": False,
        "attestation_assurance_rc": False,
        "attestation_assurance_decennale": False,
        "kbis_requis": False,
        "certifications_requises": [],
        "alertes": [],
        "resume": "Aucun document administratif identifié.",
        "confidence_overall": 0.3,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.dc_checker import analyze_dc_requirements

    result = analyze_dc_requirements("Texte sans exigences admin.")

    assert result["documents_requis"] == []
    assert result["certifications_requises"] == []


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_with_alerts(mock_llm):
    """Test with alerts for obsolete versions."""
    mock_llm.complete_json.return_value = {
        "documents_requis": [
            {"document": "DC1 v2016", "obligatoire": True, "date_validite": None, "statut": "À_FOURNIR", "details": "Version périmée", "citations": []},
        ],
        "formulaires_obligatoires": ["DC1 v2016"],
        "attestations_fiscales": False,
        "attestation_urssaf": False,
        "attestation_assurance_rc": False,
        "attestation_assurance_decennale": False,
        "kbis_requis": False,
        "certifications_requises": [],
        "alertes": ["Le DCE mentionne le DC1 version 2016 — version périmée, utiliser la version 2024"],
        "resume": "Attention: formulaire DC1 obsolète.",
        "confidence_overall": 0.8,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.dc_checker import analyze_dc_requirements

    result = analyze_dc_requirements("DCE avec DC1 v2016.")

    assert len(result["alertes"]) == 1
    assert "périmée" in result["alertes"][0]


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_text_truncation(mock_llm):
    """Test that long text is truncated."""
    mock_llm.complete_json.return_value = {
        "documents_requis": [],
        "formulaires_obligatoires": [],
        "attestations_fiscales": False,
        "attestation_urssaf": False,
        "attestation_assurance_rc": False,
        "attestation_assurance_decennale": False,
        "kbis_requis": False,
        "certifications_requises": [],
        "alertes": [],
        "resume": "",
        "confidence_overall": 0.5,
    }
    mock_llm.get_model_name.return_value = "anthropic:test"

    from app.services.dc_checker import analyze_dc_requirements

    result = analyze_dc_requirements("D" * 60_000)
    assert isinstance(result, dict)
    mock_llm.complete_json.assert_called_once()


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_llm_value_error(mock_llm):
    """Test ValueError propagation."""
    mock_llm.complete_json.side_effect = ValueError("Bad JSON from LLM")

    from app.services.dc_checker import analyze_dc_requirements

    with pytest.raises(ValueError):
        analyze_dc_requirements("Texte DCE.")


@patch("app.services.dc_checker.llm_service")
def test_analyze_dc_llm_runtime_error(mock_llm):
    """Test unexpected error propagation."""
    mock_llm.complete_json.side_effect = RuntimeError("API unavailable")

    from app.services.dc_checker import analyze_dc_requirements

    with pytest.raises(RuntimeError):
        analyze_dc_requirements("Texte DCE.")


def test_normalize_ocr_dc1():
    """Test OCR normalization for DC1 references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "DC1" in normalize_ocr_references("Fournir le D C 1")
    assert "DC1" in normalize_ocr_references("Formulaire DCl requis")
    assert "DC1" in normalize_ocr_references("D C1 obligatoire")


def test_normalize_ocr_dc2():
    """Test OCR normalization for DC2 references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "DC2" in normalize_ocr_references("D C 2 à compléter")


def test_normalize_ocr_kbis():
    """Test OCR normalization for Kbis references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "Kbis" in normalize_ocr_references("Extrait K b i s")
    assert "Kbis" in normalize_ocr_references("KBIS de moins de 3 mois")


def test_normalize_ocr_urssaf():
    """Test OCR normalization for URSSAF references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "URSSAF" in normalize_ocr_references("Attestation U R S S A F")
    assert "URSSAF" in normalize_ocr_references("URSSAE")  # common OCR confusion


def test_normalize_ocr_qualibat():
    """Test OCR normalization for Qualibat references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "Qualibat" in normalize_ocr_references("Certification Q u a l i b a t")
    assert "Qualibat" in normalize_ocr_references("Qua1ibat 1312")


def test_normalize_ocr_attri1():
    """Test OCR normalization for ATTRI1 references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "ATTRI1" in normalize_ocr_references("Formulaire A T T R I 1")


def test_normalize_ocr_dume():
    """Test OCR normalization for DUME references."""
    from app.services.dc_checker import normalize_ocr_references

    assert "DUME" in normalize_ocr_references("D U M E accepté")


def test_normalize_ocr_no_changes():
    """Test that normal text is not modified."""
    from app.services.dc_checker import normalize_ocr_references

    text = "Texte normal sans erreur OCR."
    assert normalize_ocr_references(text) == text
