"""Tests for app.services.retriever — RAG retrieval with pgvector and hybrid search."""
import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# get_dynamic_threshold
# ---------------------------------------------------------------------------

class TestGetDynamicThreshold:
    def test_high_ocr_quality_strict_threshold(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=90.0)
        assert result == 0.50

    def test_medium_ocr_quality_moderate_threshold(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=65.0)
        assert result == 0.40

    def test_low_ocr_quality_lenient_threshold(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=30.0)
        assert result == 0.30

    def test_boundary_80_is_moderate(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        # Exactly 80 should be moderate (>= 50 and <= 80)
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=80.0)
        assert result == 0.40

    def test_boundary_50_is_moderate(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=50.0)
        assert result == 0.40

    def test_boundary_49_is_lenient(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=49.0)
        assert result == 0.30

    def test_reads_from_db_when_ocr_quality_none(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 75.0 if idx == 0 else None
        mock_db.execute.return_value.fetchone.return_value = mock_row

        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=None)
        assert result == 0.40  # 75 is in 50-80 range
        mock_db.execute.assert_called_once()

    def test_defaults_to_85_when_db_returns_null(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: None
        mock_db.execute.return_value.fetchone.return_value = mock_row

        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=None)
        assert result == 0.50  # 85 > 80 -> strict

    def test_defaults_on_db_exception(self):
        from app.services.retriever import get_dynamic_threshold
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB error")

        result = get_dynamic_threshold(mock_db, "proj-1", ocr_quality=None)
        assert result == 0.50  # Default 85 -> strict


# ---------------------------------------------------------------------------
# retrieve_relevant_chunks
# ---------------------------------------------------------------------------

class TestRetrieveRelevantChunks:
    @patch("app.services.retriever.embed_query")
    def test_returns_empty_when_no_embeddings(self, mock_embed):
        from app.services.retriever import retrieve_relevant_chunks

        mock_db = MagicMock()
        # Count query returns 0
        mock_count_row = MagicMock()
        mock_count_row.__getitem__ = lambda self, idx: 0
        mock_db.execute.return_value.fetchone.return_value = mock_count_row

        # Fallback text chunks query returns nothing
        mock_db.execute.return_value.fetchall.return_value = []

        result = retrieve_relevant_chunks(mock_db, "proj-1", "test query", min_similarity=0.5)
        # Should not call embed_query since there are no embeddings
        mock_embed.assert_not_called()

    @patch("app.services.retriever.embed_query")
    def test_returns_chunks_with_similarity(self, mock_embed):
        from app.services.retriever import retrieve_relevant_chunks

        mock_embed.return_value = [0.1] * 1536
        mock_db = MagicMock()

        # Count query returns >0
        mock_count_row = MagicMock()
        mock_count_row.__getitem__ = lambda self, idx: 5
        # Set up fetchone for count query
        count_result = MagicMock()
        count_result.fetchone.return_value = mock_count_row

        # Chunk rows from pgvector query
        mock_row = MagicMock()
        mock_row.id = "chunk-1"
        mock_row.content = "Article 5 : Pénalités de retard"
        mock_row.page_start = 3
        mock_row.page_end = 4
        mock_row.doc_name = "CCAP.pdf"
        mock_row.doc_type = "CCAP"
        mock_row.distance = 0.15  # similarity = 1 - 0.15 = 0.85

        nested = MagicMock()
        vector_result = MagicMock()
        vector_result.fetchall.return_value = [mock_row]

        # First call: count query; Second call: pgvector query (inside begin_nested)
        mock_db.execute.side_effect = [count_result, vector_result]
        mock_db.begin_nested.return_value = nested

        result = retrieve_relevant_chunks(
            mock_db, "proj-1", "pénalités de retard", min_similarity=0.5
        )

        assert len(result) == 1
        assert result[0]["id"] == "chunk-1"
        assert result[0]["content"] == "Article 5 : Pénalités de retard"
        assert result[0]["similarity"] == 0.85
        assert result[0]["doc_name"] == "CCAP.pdf"

    @patch("app.services.retriever.embed_query")
    def test_fallback_on_pgvector_error(self, mock_embed):
        from app.services.retriever import retrieve_relevant_chunks

        mock_embed.return_value = [0.1] * 1536
        mock_db = MagicMock()

        # Count query returns >0
        mock_count_row = MagicMock()
        mock_count_row.__getitem__ = lambda self, idx: 5
        count_result = MagicMock()
        count_result.fetchone.return_value = mock_count_row

        # pgvector query fails
        nested = MagicMock()
        mock_db.begin_nested.return_value = nested

        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return count_result
            elif call_count["n"] == 2:
                raise Exception("pgvector extension not available")
            else:
                # Fallback text query
                fallback_result = MagicMock()
                fallback_result.fetchall.return_value = []
                return fallback_result

        mock_db.execute.side_effect = side_effect

        result = retrieve_relevant_chunks(
            mock_db, "proj-1", "test query", min_similarity=0.5
        )
        # Should return empty from fallback (no rows)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# _fallback_text_chunks
# ---------------------------------------------------------------------------

class TestFallbackTextChunks:
    def test_returns_chunks_with_conservative_score(self):
        from app.services.retriever import _fallback_text_chunks

        mock_row = MagicMock()
        mock_row.id = "chunk-fb-1"
        mock_row.content = "Texte brut du document"
        mock_row.page_start = 1
        mock_row.page_end = 2
        mock_row.doc_name = "DPGF.pdf"
        mock_row.doc_type = "DPGF"

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [mock_row]

        result = _fallback_text_chunks(mock_db, "proj-1", top_k=10)
        assert len(result) == 1
        assert result[0]["similarity"] == 0.35  # Conservative score
        assert result[0]["doc_type"] == "DPGF"

    def test_returns_empty_on_db_error(self):
        from app.services.retriever import _fallback_text_chunks

        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB connection lost")

        result = _fallback_text_chunks(mock_db, "proj-1")
        assert result == []


# ---------------------------------------------------------------------------
# format_context
# ---------------------------------------------------------------------------

class TestFormatContext:
    def test_empty_chunks_returns_no_context_message(self):
        from app.services.retriever import format_context
        result = format_context([])
        assert "Aucun contexte" in result

    def test_formats_single_chunk(self):
        from app.services.retriever import format_context
        chunks = [{
            "doc_name": "CCAP.pdf",
            "page_start": 5,
            "page_end": 6,
            "content": "Article 10 : Délai d'exécution est de 12 mois.",
        }]
        result = format_context(chunks)
        assert "CCAP.pdf" in result
        assert "p.5" in result
        assert "Article 10" in result

    def test_formats_multiple_chunks_with_separator(self):
        from app.services.retriever import format_context
        chunks = [
            {"doc_name": "CCAP.pdf", "page_start": 1, "page_end": 2, "content": "Chunk 1"},
            {"doc_name": "DPGF.pdf", "page_start": 3, "page_end": 4, "content": "Chunk 2"},
        ]
        result = format_context(chunks)
        assert "---" in result
        assert "Chunk 1" in result
        assert "Chunk 2" in result


# ---------------------------------------------------------------------------
# get_max_similarity
# ---------------------------------------------------------------------------

class TestGetMaxSimilarity:
    def test_empty_chunks_returns_zero(self):
        from app.services.retriever import get_max_similarity
        assert get_max_similarity([]) == 0.0

    def test_returns_max_value(self):
        from app.services.retriever import get_max_similarity
        chunks = [
            {"similarity": 0.6},
            {"similarity": 0.9},
            {"similarity": 0.75},
        ]
        assert get_max_similarity(chunks) == 0.9

    def test_handles_missing_similarity_key(self):
        from app.services.retriever import get_max_similarity
        chunks = [{"content": "no similarity field"}]
        assert get_max_similarity(chunks) == 0.0


# ---------------------------------------------------------------------------
# expand_query
# ---------------------------------------------------------------------------

class TestExpandQuery:
    def test_no_synonyms_returns_original_only(self):
        from app.services.retriever import expand_query
        variants = expand_query("bonjour le monde")
        assert len(variants) == 1
        assert variants[0] == "bonjour le monde"

    def test_expands_known_term(self):
        from app.services.retriever import expand_query
        variants = expand_query("sous-traitance conditions")
        assert len(variants) >= 2
        assert variants[0] == "sous-traitance conditions"
        # Variant should contain synonyms
        assert any("sous-traitant" in v or "co-traitance" in v for v in variants[1:])

    def test_expands_multiple_terms(self):
        from app.services.retriever import expand_query
        variants = expand_query("pénalités et garantie")
        # Should have at least 2 variants
        assert len(variants) >= 2

    def test_original_always_first(self):
        from app.services.retriever import expand_query
        query = "délai d'exécution"
        variants = expand_query(query)
        assert variants[0] == query

    def test_max_three_variants(self):
        from app.services.retriever import expand_query
        # Even with many matching terms, should produce at most 3 variants
        variants = expand_query("sous-traitance pénalités délai garantie prix assurance")
        assert len(variants) <= 3


# ---------------------------------------------------------------------------
# retrieve_hybrid
# ---------------------------------------------------------------------------

class TestRetrieveHybrid:
    @patch("app.services.retriever._bm25_search")
    @patch("app.services.retriever.retrieve_relevant_chunks")
    def test_vector_only_when_bm25_empty(self, mock_vector, mock_bm25):
        from app.services.retriever import retrieve_hybrid

        mock_vector.return_value = [
            {"id": "c1", "content": "text 1", "similarity": 0.8, "doc_id": "d1"},
            {"id": "c2", "content": "text 2", "similarity": 0.7, "doc_id": "d2"},
        ]
        mock_bm25.return_value = []

        mock_db = MagicMock()
        result = retrieve_hybrid(mock_db, "proj-1", "test query", top_k=5)

        assert len(result) == 2
        assert result[0]["id"] == "c1"
        assert "score" in result[0]

    @patch("app.services.retriever._bm25_search")
    @patch("app.services.retriever.retrieve_relevant_chunks")
    def test_rrf_fusion(self, mock_vector, mock_bm25):
        from app.services.retriever import retrieve_hybrid

        mock_vector.return_value = [
            {"id": "c1", "content": "text 1", "similarity": 0.9, "doc_id": "d1"},
            {"id": "c2", "content": "text 2", "similarity": 0.8, "doc_id": "d2"},
        ]
        mock_bm25.return_value = [
            {"id": "c2", "content": "text 2", "doc_id": "d2", "bm25_rank": 0.5},
            {"id": "c3", "content": "text 3", "doc_id": "d3", "bm25_rank": 0.3},
        ]

        mock_db = MagicMock()
        result = retrieve_hybrid(mock_db, "proj-1", "test query", top_k=5)

        # c2 appears in both lists, should have highest RRF score
        ids = [r["id"] for r in result]
        assert "c2" in ids
        assert "c1" in ids
        assert "c3" in ids

        # c2 should be ranked first (highest combined RRF)
        assert result[0]["id"] == "c2"

    @patch("app.services.retriever._bm25_search")
    @patch("app.services.retriever.retrieve_relevant_chunks")
    def test_respects_top_k(self, mock_vector, mock_bm25):
        from app.services.retriever import retrieve_hybrid

        mock_vector.return_value = [
            {"id": f"c{i}", "content": f"text {i}", "similarity": 0.9 - i * 0.05, "doc_id": f"d{i}"}
            for i in range(10)
        ]
        mock_bm25.return_value = [
            {"id": f"b{i}", "content": f"bm25 {i}", "doc_id": f"d{i}", "bm25_rank": 0.5 - i * 0.05}
            for i in range(10)
        ]

        mock_db = MagicMock()
        result = retrieve_hybrid(mock_db, "proj-1", "query", top_k=3)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# rerank_with_llm
# ---------------------------------------------------------------------------

class TestRerankWithLLM:
    def test_returns_unchanged_if_within_top_k(self):
        from app.services.retriever import rerank_with_llm
        chunks = [{"id": f"c{i}", "content": f"text {i}"} for i in range(5)]
        result = rerank_with_llm(chunks, "query", top_k=10)
        assert result == chunks

    @patch("app.services.llm.llm_service")
    def test_reranks_and_filters(self, mock_llm):
        from app.services.retriever import rerank_with_llm

        chunks = [{"id": f"c{i}", "content": f"text {i}"} for i in range(15)]
        # Scores: some above 5, some below
        scores = [8, 3, 9, 2, 7, 1, 6, 4, 5, 10, 3, 2, 7, 8, 6]
        mock_llm.complete_json.return_value = {"scores": scores}

        result = rerank_with_llm(chunks, "query", top_k=5)
        assert len(result) == 5
        # First result should be the one with score 10 (index 9)
        assert result[0]["id"] == "c9"

    @patch("app.services.llm.llm_service")
    def test_returns_original_on_llm_error(self, mock_llm):
        from app.services.retriever import rerank_with_llm

        chunks = [{"id": f"c{i}", "content": f"text {i}"} for i in range(15)]
        mock_llm.complete_json.side_effect = Exception("LLM error")

        result = rerank_with_llm(chunks, "query", top_k=5)
        assert len(result) == 5

    @patch("app.services.llm.llm_service")
    def test_returns_original_on_score_count_mismatch(self, mock_llm):
        from app.services.retriever import rerank_with_llm

        chunks = [{"id": f"c{i}", "content": f"text {i}"} for i in range(15)]
        mock_llm.complete_json.return_value = {"scores": [8, 9]}  # Wrong count

        result = rerank_with_llm(chunks, "query", top_k=5)
        assert len(result) == 5
