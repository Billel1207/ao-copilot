"""Tests for app.services.embedder — OpenAI embedding service."""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# embed_texts
# ---------------------------------------------------------------------------

class TestEmbedTexts:
    @patch("app.services.embedder._client")
    def test_embed_single_text(self, mock_client):
        mock_item = MagicMock()
        mock_item.embedding = [0.1] * 1536
        mock_item.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response

        from app.services.embedder import embed_texts
        result = embed_texts(["Hello world"])
        assert len(result) == 1
        assert len(result[0]) == 1536

    @patch("app.services.embedder._client")
    def test_embed_multiple_texts(self, mock_client):
        items = []
        for i in range(3):
            item = MagicMock()
            item.embedding = [float(i) / 10] * 1536
            item.index = i
            items.append(item)

        mock_response = MagicMock()
        mock_response.data = items
        mock_client.embeddings.create.return_value = mock_response

        from app.services.embedder import embed_texts
        result = embed_texts(["text1", "text2", "text3"])
        assert len(result) == 3

    @patch("app.services.embedder._client")
    def test_embed_empty_list(self, mock_client):
        from app.services.embedder import embed_texts
        result = embed_texts([])
        assert result == []
        mock_client.embeddings.create.assert_not_called()

    @patch("app.services.embedder._client")
    def test_embed_texts_batching(self, mock_client):
        """With >100 texts, should batch by 100."""
        texts = [f"text_{i}" for i in range(150)]

        def create_response(model, input):
            items = []
            for i, _ in enumerate(input):
                item = MagicMock()
                item.embedding = [0.5] * 1536
                item.index = i
                items.append(item)
            resp = MagicMock()
            resp.data = items
            return resp

        mock_client.embeddings.create.side_effect = create_response

        from app.services.embedder import embed_texts
        result = embed_texts(texts)
        assert len(result) == 150
        assert mock_client.embeddings.create.call_count == 2  # 100 + 50

    @patch("app.services.embedder._client")
    def test_embed_texts_sorts_by_index(self, mock_client):
        """Results should be sorted by index."""
        item0 = MagicMock()
        item0.embedding = [0.0] * 1536
        item0.index = 1
        item1 = MagicMock()
        item1.embedding = [1.0] * 1536
        item1.index = 0
        mock_response = MagicMock()
        mock_response.data = [item0, item1]  # Out of order
        mock_client.embeddings.create.return_value = mock_response

        from app.services.embedder import embed_texts
        result = embed_texts(["a", "b"])
        # Index 0 should come first
        assert result[0][0] == 1.0
        assert result[1][0] == 0.0


# ---------------------------------------------------------------------------
# embed_query
# ---------------------------------------------------------------------------

class TestEmbedQuery:
    @patch("app.services.embedder._client")
    def test_embed_query_returns_vector(self, mock_client):
        mock_item = MagicMock()
        mock_item.embedding = [0.42] * 1536
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response

        from app.services.embedder import embed_query
        result = embed_query("What is the deadline?")
        assert len(result) == 1536
        assert result[0] == 0.42

    @patch("app.services.embedder._client")
    def test_embed_query_calls_api_correctly(self, mock_client):
        mock_item = MagicMock()
        mock_item.embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response

        from app.services.embedder import embed_query
        embed_query("search query")
        mock_client.embeddings.create.assert_called_once()
        call_kwargs = mock_client.embeddings.create.call_args[1]
        assert call_kwargs["input"] == ["search query"]
