"""Tests for app.services.chunker — text chunking for RAG pipeline."""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------

class TestCountTokens:
    def test_count_tokens_with_short_text(self):
        from app.services.chunker import count_tokens
        result = count_tokens("Hello world")
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_with_empty_string(self):
        from app.services.chunker import count_tokens
        result = count_tokens("")
        assert result == 0

    def test_count_tokens_with_long_text(self):
        from app.services.chunker import count_tokens
        text = "mot " * 500
        result = count_tokens(text)
        assert result > 100

    @patch("app.services.chunker.tiktoken")
    def test_count_tokens_fallback_on_error(self, mock_tiktoken):
        """When tiktoken fails, fallback to len(text)//4."""
        mock_tiktoken.get_encoding.side_effect = Exception("tiktoken unavailable")
        from app.services.chunker import count_tokens
        result = count_tokens("a" * 100)
        assert result == 25  # 100 // 4


# ---------------------------------------------------------------------------
# build_page_text
# ---------------------------------------------------------------------------

class TestBuildPageText:
    def test_basic_pages(self):
        from app.services.chunker import build_page_text
        pages = [
            {"page_num": 1, "raw_text": "Page one content"},
            {"page_num": 2, "raw_text": "Page two content"},
        ]
        result = build_page_text(pages)
        assert len(result) == 2
        assert result[0] == (1, "Page one content")
        assert result[1] == (2, "Page two content")

    def test_skips_empty_pages(self):
        from app.services.chunker import build_page_text
        pages = [
            {"page_num": 1, "raw_text": "Has content"},
            {"page_num": 2, "raw_text": ""},
            {"page_num": 3, "raw_text": None},
            {"page_num": 4, "raw_text": "Also has content"},
        ]
        result = build_page_text(pages)
        assert len(result) == 2
        assert result[0][0] == 1
        assert result[1][0] == 4

    def test_empty_list(self):
        from app.services.chunker import build_page_text
        assert build_page_text([]) == []


# ---------------------------------------------------------------------------
# contextualize_chunk
# ---------------------------------------------------------------------------

class TestContextualizeChunk:
    def test_basic_context(self):
        from app.services.chunker import contextualize_chunk
        result = contextualize_chunk("Le delai est de 30 jours", "CCAP", "Renovation.pdf")
        assert result.startswith("[CCAP: Renovation")
        assert "Le delai est de 30 jours" in result

    def test_with_section_header(self):
        from app.services.chunker import contextualize_chunk
        result = contextualize_chunk("content here", "RC", "doc.pdf", "Article 5 - Delais")
        assert "Article 5 - Delais" in result
        assert "[RC" in result

    def test_without_doc_name(self):
        from app.services.chunker import contextualize_chunk
        result = contextualize_chunk("text", "DPGF", "")
        assert result.startswith("[DPGF] text")

    def test_filename_extension_stripped(self):
        from app.services.chunker import contextualize_chunk
        result = contextualize_chunk("text", "AE", "document.pdf")
        assert ".pdf" not in result.split("]")[0]  # extension removed from prefix

    def test_no_doc_type(self):
        from app.services.chunker import contextualize_chunk
        result = contextualize_chunk("text", "", "")
        assert result.startswith("[") and "] text" in result


# ---------------------------------------------------------------------------
# STRUCTURE_PATTERN
# ---------------------------------------------------------------------------

class TestStructurePattern:
    def test_matches_article(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("Article 5 - Delais d'execution")

    def test_matches_chapitre(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("Chapitre III : Conditions")

    def test_matches_section(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("Section 2 Modalites")

    def test_matches_titre(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("TITRE IV - PENALITES")

    def test_matches_numbered_subsection(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("3.2 Conditions de paiement")

    def test_no_match_regular_text(self):
        from app.services.chunker import STRUCTURE_PATTERN
        assert STRUCTURE_PATTERN.search("Le titulaire devra respecter les delais") is None


# ---------------------------------------------------------------------------
# _find_page_range
# ---------------------------------------------------------------------------

class TestFindPageRange:
    def test_single_page(self):
        from app.services.chunker import _find_page_range
        page_positions = [(1, 0, 100), (2, 100, 200)]
        start, end = _find_page_range(10, 50, page_positions)
        assert start == 1
        assert end == 1

    def test_spanning_two_pages(self):
        from app.services.chunker import _find_page_range
        page_positions = [(1, 0, 100), (2, 100, 200)]
        start, end = _find_page_range(80, 120, page_positions)
        assert start == 1
        assert end == 2

    def test_no_overlap_defaults_to_1(self):
        from app.services.chunker import _find_page_range
        page_positions = [(5, 500, 600)]
        start, end = _find_page_range(0, 10, page_positions)
        assert start == 1
        assert end == 1


# ---------------------------------------------------------------------------
# chunk_pages — integration test
# ---------------------------------------------------------------------------

class TestChunkPages:
    def test_empty_pages(self):
        from app.services.chunker import chunk_pages
        result = chunk_pages([])
        assert result == []

    def test_pages_with_only_empty_text(self):
        from app.services.chunker import chunk_pages
        pages = [{"page_num": 1, "raw_text": ""}, {"page_num": 2, "raw_text": None}]
        result = chunk_pages(pages)
        assert result == []

    def test_simple_chunking(self):
        from app.services.chunker import chunk_pages
        pages = [{"page_num": 1, "raw_text": "Short content for testing."}]
        result = chunk_pages(pages)
        assert len(result) >= 1
        assert result[0].page_start == 1
        assert result[0].chunk_index == 0
        assert result[0].token_count > 0

    def test_structured_doc_type_ccap(self):
        from app.services.chunker import chunk_pages
        text = (
            "Preambule du marche.\n\n"
            "Article 1 - Objet du marche\n"
            "Le present marche a pour objet la construction d'un batiment.\n" * 5 + "\n"
            "Article 2 - Duree du marche\n"
            "La duree du marche est de 12 mois a compter de la notification.\n" * 5 + "\n"
            "Article 3 - Prix\n"
            "Les prix sont fermes et definitifs.\n" * 5
        )
        pages = [{"page_num": 1, "raw_text": text}]
        result = chunk_pages(pages, doc_name="CCAP.pdf", doc_type="ccap")
        assert len(result) >= 2
        # Chunks should have context prefix for CCAP
        assert any("[ccap" in c.content.lower() or "[CCAP" in c.content for c in result)

    def test_unstructured_doc_type(self):
        from app.services.chunker import chunk_pages
        text = "Lorem ipsum dolor sit amet. " * 200
        pages = [{"page_num": 1, "raw_text": text}]
        result = chunk_pages(pages, doc_type="dpgf")
        assert len(result) >= 1

    def test_multipage_chunking(self):
        from app.services.chunker import chunk_pages
        pages = [
            {"page_num": 1, "raw_text": "Page one content. " * 50},
            {"page_num": 2, "raw_text": "Page two content. " * 50},
            {"page_num": 3, "raw_text": "Page three content. " * 50},
        ]
        result = chunk_pages(pages)
        assert len(result) >= 1
        # Verify page mapping exists
        for chunk in result:
            assert chunk.page_start >= 1
            assert chunk.page_end >= chunk.page_start


# ---------------------------------------------------------------------------
# TextChunk dataclass
# ---------------------------------------------------------------------------

class TestTextChunk:
    def test_text_chunk_creation(self):
        from app.services.chunker import TextChunk
        tc = TextChunk(
            content="test content",
            chunk_index=0,
            page_start=1,
            page_end=1,
            token_count=10,
        )
        assert tc.content == "test content"
        assert tc.context_prefix == ""  # default
