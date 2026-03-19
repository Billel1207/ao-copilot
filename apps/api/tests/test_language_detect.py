"""Tests pour app/services/language_detect.py — détection de langue FR/EN."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.language_detect import detect_language, detect_project_language


# ── detect_language() ────────────────────────────────────────────────────────

class TestDetectLanguage:
    """Tests unitaires pour detect_language()."""

    def test_french_text_returns_fr(self):
        text = (
            "Le marché public de travaux concerne la rénovation du bâtiment "
            "administratif situé dans la commune de Lyon. Le candidat doit "
            "fournir les attestations d'assurance et les certificats de "
            "qualification pour les lots de gros oeuvre et de second oeuvre. "
            "La date limite de soumission des offres est fixée au 15 avril."
        )
        assert detect_language(text) == "fr"

    def test_english_text_returns_en(self):
        text = (
            "The procurement procedure for this tender shall be conducted "
            "in accordance with the framework agreement. The contractor must "
            "submit the proposal and all required documents by the deadline. "
            "The evaluation criteria include technical capacity and financial "
            "standing. The contracting authority will assess the eligibility "
            "of each bidder based on the requirements set forth in this notice. "
            "All submissions must be made through the electronic procurement "
            "platform by the submission deadline specified in the contract notice."
        )
        assert detect_language(text) == "en"

    def test_empty_text_returns_fr_default(self):
        assert detect_language("") == "fr"

    def test_none_text_returns_fr_default(self):
        assert detect_language(None) == "fr"

    def test_short_text_returns_fr_default(self):
        assert detect_language("Hello world") == "fr"

    def test_very_short_text_under_50_chars(self):
        assert detect_language("Marché de travaux") == "fr"

    def test_mixed_text_majority_french(self):
        text = (
            "Le cahier des clauses administratives particulières définit "
            "les conditions du marché public. Le candidat doit fournir "
            "un mémoire technique et les attestations requises pour "
            "la soumission de son offre. Les travaux de rénovation "
            "concernent le bâtiment principal de la mairie. "
            "The deadline for submission is April 15."
        )
        assert detect_language(text) == "fr"

    def test_mixed_text_majority_english(self):
        text = (
            "The tender documents shall be submitted by the contractor "
            "to the contracting authority. The evaluation of proposals "
            "will be based on the criteria specified in the procurement "
            "notice. The bidder must demonstrate the technical capacity "
            "and financial standing required for this framework agreement. "
            "The submission deadline is mandatory and must be respected "
            "by all participating contractors in this procurement process. "
            "Le marché concerne des travaux."
        )
        assert detect_language(text) == "en"

    def test_text_with_no_markers(self):
        """Text with no recognized markers defaults to fr."""
        text = "123456789 " * 10  # Numbers only, > 50 chars
        assert detect_language(text) == "fr"

    def test_text_with_accented_french_words(self):
        text = (
            "Le règlement de la consultation précise les modalités de "
            "soumission des offres. Le délai d'exécution des travaux "
            "est fixé à douze mois. Les pièces administratives et "
            "techniques doivent être fournies par le candidat."
        )
        assert detect_language(text) == "fr"


# ── detect_project_language() ────────────────────────────────────────────────

class TestDetectProjectLanguage:
    """Tests pour detect_project_language() avec mocks DB."""

    def test_no_documents_returns_fr(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.all.return_value = []

        result = detect_project_language(mock_db, "00000000-0000-0000-0000-000000000001")
        assert result == "fr"

    def test_french_documents_returns_fr(self):
        mock_db = MagicMock()

        # Create mock documents
        mock_doc = MagicMock()
        mock_doc.id = "doc-1"

        # Mock pages with French text
        mock_page = MagicMock()
        mock_page.raw_text = (
            "Le marché public de travaux concerne la rénovation du bâtiment "
            "administratif. Le candidat doit fournir les attestations et "
            "les certificats de qualification pour les lots de gros oeuvre."
        )

        mock_query_docs = MagicMock()
        mock_query_pages = MagicMock()

        # First call returns docs, second returns pages
        def query_side_effect(model):
            from app.models.document import AoDocument, DocumentPage
            if model is AoDocument:
                return mock_query_docs
            return mock_query_pages

        mock_db.query.side_effect = query_side_effect
        mock_query_docs.filter_by.return_value = mock_query_docs
        mock_query_docs.all.return_value = [mock_doc]

        mock_query_pages.filter_by.return_value = mock_query_pages
        mock_query_pages.order_by.return_value = mock_query_pages
        mock_query_pages.limit.return_value = mock_query_pages
        mock_query_pages.all.return_value = [mock_page]

        result = detect_project_language(mock_db, "00000000-0000-0000-0000-000000000001")
        assert result == "fr"

    def test_english_documents_returns_en(self):
        mock_db = MagicMock()

        mock_doc1 = MagicMock()
        mock_doc1.id = "doc-1"
        mock_doc2 = MagicMock()
        mock_doc2.id = "doc-2"

        mock_page_en = MagicMock()
        mock_page_en.raw_text = (
            "The procurement procedure for this tender shall be conducted "
            "in accordance with the framework agreement. The contractor must "
            "submit the proposal and all required documents by the deadline. "
            "The evaluation criteria include technical capacity and financial "
            "standing of the bidder for this procurement process."
        )

        mock_query_docs = MagicMock()
        mock_query_pages = MagicMock()

        def query_side_effect(model):
            from app.models.document import AoDocument, DocumentPage
            if model is AoDocument:
                return mock_query_docs
            return mock_query_pages

        mock_db.query.side_effect = query_side_effect
        mock_query_docs.filter_by.return_value = mock_query_docs
        mock_query_docs.all.return_value = [mock_doc1, mock_doc2]

        mock_query_pages.filter_by.return_value = mock_query_pages
        mock_query_pages.order_by.return_value = mock_query_pages
        mock_query_pages.limit.return_value = mock_query_pages
        mock_query_pages.all.return_value = [mock_page_en]

        result = detect_project_language(mock_db, "00000000-0000-0000-0000-000000000001")
        assert result == "en"
