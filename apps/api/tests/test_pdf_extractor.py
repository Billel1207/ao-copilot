"""Tests pour app/services/pdf_extractor.py — extraction et détection de documents.

Teste les fonctions pures (detect_section, detect_doc_type_from_content,
has_sufficient_text, clean_text, compute_document_ocr_quality) sans
dépendance à fitz/Tesseract.
"""
import pytest

from app.services.pdf_extractor import (
    detect_section,
    detect_doc_type_from_content,
    has_sufficient_text,
    clean_text,
    compute_document_ocr_quality,
    PageResult,
    OCR_THRESHOLD,
    OCR_FAILURE_MARKER,
    DOC_TYPE_PATTERNS,
    SECTION_PATTERNS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# detect_section
# ═══════════════════════════════════════════════════════════════════════════════


class TestDetectSection:
    def test_article_header(self):
        assert detect_section("Article 5 — Pénalités de retard") == "section"

    def test_chapitre_header(self):
        assert detect_section("Chapitre 2 : Clauses financières") == "section"

    def test_section_header(self):
        assert detect_section("Section 3 - Dispositions techniques") == "section"

    def test_rc_header(self):
        assert detect_section("RC\nRèglement de consultation") == "RC"

    def test_cctp_header(self):
        assert detect_section("CCTP - Cahier des clauses techniques") == "CCTP"

    def test_ccap_header(self):
        assert detect_section("CCAP du marché public") == "CCAP"

    def test_dpgf_header(self):
        assert detect_section("DPGF — Décomposition du prix global") == "DPGF"

    def test_bpu_header(self):
        assert detect_section("BPU — Bordereau des Prix Unitaires") == "BPU"

    def test_ae_header(self):
        assert detect_section("Acte d'engagement") == "AE"

    def test_no_match(self):
        assert detect_section("Lorem ipsum dolor sit amet") is None

    def test_empty_text(self):
        assert detect_section("") is None

    def test_case_insensitive(self):
        assert detect_section("article 1 - objet du marché") == "section"


# ═══════════════════════════════════════════════════════════════════════════════
# detect_doc_type_from_content
# ═══════════════════════════════════════════════════════════════════════════════


class TestDetectDocTypeFromContent:
    def test_rc_detection(self):
        text = (
            "Règlement de consultation\n"
            "Objet de la consultation\n"
            "Critères d'attribution du marché\n"
            "Date limite de remise des offres : 15/07/2026"
        )
        assert detect_doc_type_from_content(text) == "RC"

    def test_cctp_detection(self):
        text = (
            "CCTP\n"
            "Cahier des clauses techniques particulières\n"
            "Prescriptions techniques pour les travaux de rénovation"
        )
        assert detect_doc_type_from_content(text) == "CCTP"

    def test_ccap_detection(self):
        text = (
            "CCAP\n"
            "Cahier des clauses administratives particulières\n"
            "Pénalités de retard : 1/1000 par jour\n"
            "Retenue de garantie : 5%"
        )
        assert detect_doc_type_from_content(text) == "CCAP"

    def test_dpgf_detection(self):
        text = (
            "Décomposition du prix global et forfaitaire\n"
            "DPGF\n"
            "Prix forfaitaire des prestations"
        )
        assert detect_doc_type_from_content(text) == "DPGF"

    def test_ae_detection(self):
        text = (
            "Acte d'engagement\n"
            "Le candidat s'engage à réaliser les travaux\n"
            "Montant total du marché"
        )
        assert detect_doc_type_from_content(text) == "AE"

    def test_too_short_text(self):
        assert detect_doc_type_from_content("RC") is None

    def test_empty_text(self):
        assert detect_doc_type_from_content("") is None

    def test_none_text(self):
        assert detect_doc_type_from_content(None) is None

    def test_no_match(self):
        text = "Un texte quelconque sans aucun marqueur de document DCE identifiable."
        assert detect_doc_type_from_content(text) is None

    def test_requires_2_matches(self):
        """Un seul pattern ne suffit pas (seuil anti-faux-positifs)."""
        text = "x" * 100 + "Retenue de garantie" + "x" * 100
        # Only 1 match for CCAP → should return None
        assert detect_doc_type_from_content(text) is None

    def test_uses_first_3000_chars(self):
        text = "x" * 3500 + "CCAP\nCahier des clauses administratives particulières"
        assert detect_doc_type_from_content(text) is None  # beyond 3000 chars


# ═══════════════════════════════════════════════════════════════════════════════
# has_sufficient_text
# ═══════════════════════════════════════════════════════════════════════════════


class TestHasSufficientText:
    def test_empty_pages(self):
        assert has_sufficient_text([]) is False

    def test_all_pages_sufficient(self):
        pages = [
            PageResult(page_num=i, raw_text="x" * 200, char_count=200,
                       section=None, needs_ocr=False)
            for i in range(5)
        ]
        assert has_sufficient_text(pages) is True

    def test_no_pages_sufficient(self):
        pages = [
            PageResult(page_num=i, raw_text="hi", char_count=2,
                       section=None, needs_ocr=True, ocr_confidence=20.0)
            for i in range(5)
        ]
        assert has_sufficient_text(pages) is False

    def test_threshold_boundary(self):
        """30% threshold — 3/10 pages should be enough."""
        pages = [
            PageResult(page_num=i, raw_text="x" * 200, char_count=200,
                       section=None, needs_ocr=False)
            for i in range(3)
        ] + [
            PageResult(page_num=i, raw_text="hi", char_count=2,
                       section=None, needs_ocr=True)
            for i in range(3, 10)
        ]
        assert has_sufficient_text(pages) is True

    def test_below_threshold(self):
        """2/10 pages < 30% threshold."""
        pages = [
            PageResult(page_num=i, raw_text="x" * 200, char_count=200,
                       section=None, needs_ocr=False)
            for i in range(2)
        ] + [
            PageResult(page_num=i, raw_text="hi", char_count=2,
                       section=None, needs_ocr=True)
            for i in range(2, 10)
        ]
        assert has_sufficient_text(pages) is False

    def test_custom_threshold(self):
        pages = [
            PageResult(page_num=1, raw_text="x" * 200, char_count=200,
                       section=None, needs_ocr=False),
            PageResult(page_num=2, raw_text="hi", char_count=2,
                       section=None, needs_ocr=True),
        ]
        assert has_sufficient_text(pages, threshold=0.5) is True


# ═══════════════════════════════════════════════════════════════════════════════
# clean_text
# ═══════════════════════════════════════════════════════════════════════════════


class TestCleanText:
    def test_removes_short_lines(self):
        text = "Titre du document\nabc\nContenu principal du document"
        result = clean_text(text)
        assert "abc" not in result
        assert "Titre du document" in result

    def test_preserves_long_lines(self):
        text = "Ligne suffisamment longue pour être conservée"
        assert clean_text(text) == text

    def test_empty_text(self):
        assert clean_text("") == ""

    def test_all_short_lines(self):
        text = "a\nb\nc\nd"
        assert clean_text(text) == ""


# ═══════════════════════════════════════════════════════════════════════════════
# compute_document_ocr_quality
# ═══════════════════════════════════════════════════════════════════════════════


class TestComputeDocumentOcrQuality:
    def test_no_ocr_pages(self):
        pages = [
            PageResult(page_num=1, raw_text="text", char_count=100,
                       section=None, needs_ocr=False),
        ]
        result = compute_document_ocr_quality(pages)
        assert result["ocr_score"] is None
        assert result["pages_ocr_count"] == 0
        assert result["warning"] is None

    def test_good_ocr(self):
        pages = [
            PageResult(page_num=1, raw_text="text", char_count=100,
                       section=None, needs_ocr=True, ocr_confidence=92.0),
            PageResult(page_num=2, raw_text="text", char_count=100,
                       section=None, needs_ocr=True, ocr_confidence=88.0),
        ]
        result = compute_document_ocr_quality(pages)
        assert result["ocr_score"] == 90.0
        assert result["pages_ocr_count"] == 2
        assert result["pages_low_quality"] == 0
        assert result["warning"] is None

    def test_low_ocr_warning(self):
        pages = [
            PageResult(page_num=1, raw_text="text", char_count=20,
                       section=None, needs_ocr=True, ocr_confidence=40.0),
        ]
        result = compute_document_ocr_quality(pages)
        assert result["ocr_score"] == 40.0
        assert "très faible" in result["warning"]

    def test_medium_ocr_warning(self):
        pages = [
            PageResult(page_num=1, raw_text="text", char_count=20,
                       section=None, needs_ocr=True, ocr_confidence=65.0),
        ]
        result = compute_document_ocr_quality(pages)
        assert "moyenne" in result["warning"]

    def test_mixed_ocr_and_text_pages(self):
        pages = [
            PageResult(page_num=1, raw_text="text", char_count=200,
                       section=None, needs_ocr=False),
            PageResult(page_num=2, raw_text="text", char_count=20,
                       section=None, needs_ocr=True, ocr_confidence=80.0),
        ]
        result = compute_document_ocr_quality(pages)
        assert result["pages_ocr_count"] == 1

    def test_empty_pages(self):
        result = compute_document_ocr_quality([])
        assert result["ocr_score"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# Constants integrity
# ═══════════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_ocr_threshold_positive(self):
        assert OCR_THRESHOLD > 0

    def test_failure_marker_not_empty(self):
        assert len(OCR_FAILURE_MARKER) > 0

    def test_doc_type_patterns_cover_main_types(self):
        expected = {"RC", "CCTP", "CCAP", "DPGF", "BPU", "AE"}
        assert expected.issubset(set(DOC_TYPE_PATTERNS.keys()))

    def test_section_patterns_not_empty(self):
        assert len(SECTION_PATTERNS) > 0
