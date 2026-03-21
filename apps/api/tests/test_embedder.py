"""Tests for app.services.embedder — OpenAI/Mistral embedding service."""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helper — build a mock OpenAI client for embedding tests
# ---------------------------------------------------------------------------

def _make_mock_openai(responses=None):
    """Create a mock OpenAI client with embeddings.create() configured."""
    mock_client = MagicMock()
    if responses is not None:
        mock_client.embeddings.create.side_effect = responses
    return mock_client


def _make_embed_response(embeddings: list[list[float]]):
    """Build a fake OpenAI embeddings response."""
    items = []
    for i, emb in enumerate(embeddings):
        item = MagicMock()
        item.embedding = emb
        item.index = i
        items.append(item)
    resp = MagicMock()
    resp.data = items
    return resp


# ---------------------------------------------------------------------------
# embed_texts
# ---------------------------------------------------------------------------

class TestEmbedTexts:
    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_single_text(self, mock_get_openai, _mock_mistral):
        mock_client = MagicMock()
        mock_item = MagicMock()
        mock_item.embedding = [0.1] * 1536
        mock_item.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_texts
        result = embed_texts(["Hello world"])
        assert len(result) == 1
        assert len(result[0]) == 1536

    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_multiple_texts(self, mock_get_openai, _mock_mistral):
        mock_client = MagicMock()
        items = []
        for i in range(3):
            item = MagicMock()
            item.embedding = [float(i) / 10] * 1536
            item.index = i
            items.append(item)

        mock_response = MagicMock()
        mock_response.data = items
        mock_client.embeddings.create.return_value = mock_response
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_texts
        result = embed_texts(["text1", "text2", "text3"])
        assert len(result) == 3

    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_empty_list(self, mock_get_openai, _mock_mistral):
        from app.services.embedder import embed_texts
        result = embed_texts([])
        assert result == []
        mock_get_openai.assert_not_called()

    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_texts_batching(self, mock_get_openai, _mock_mistral):
        """With >100 texts, should batch by 100."""
        mock_client = MagicMock()
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
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_texts
        result = embed_texts(texts)
        assert len(result) == 150
        assert mock_client.embeddings.create.call_count == 2  # 100 + 50

    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_texts_sorts_by_index(self, mock_get_openai, _mock_mistral):
        """Results should be sorted by index."""
        mock_client = MagicMock()
        item0 = MagicMock()
        item0.embedding = [0.0] * 1536
        item0.index = 1
        item1 = MagicMock()
        item1.embedding = [1.0] * 1536
        item1.index = 0
        mock_response = MagicMock()
        mock_response.data = [item0, item1]  # Out of order
        mock_client.embeddings.create.return_value = mock_response
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_texts
        result = embed_texts(["a", "b"])
        # Index 0 should come first
        assert result[0][0] == 1.0
        assert result[1][0] == 0.0


# ---------------------------------------------------------------------------
# embed_query
# ---------------------------------------------------------------------------

class TestEmbedQuery:
    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_query_returns_vector(self, mock_get_openai, _mock_mistral):
        mock_client = MagicMock()
        mock_item = MagicMock()
        mock_item.embedding = [0.42] * 1536
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_query
        result = embed_query("What is the deadline?")
        assert len(result) == 1536
        assert result[0] == 0.42

    @patch("app.services.embedder._use_mistral", return_value=False)
    @patch("app.services.embedder._get_openai")
    def test_embed_query_calls_api_correctly(self, mock_get_openai, _mock_mistral):
        mock_client = MagicMock()
        mock_item = MagicMock()
        mock_item.embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_openai.return_value = mock_client

        from app.services.embedder import embed_query
        embed_query("search query")
        mock_client.embeddings.create.assert_called_once()
        call_kwargs = mock_client.embeddings.create.call_args[1]
        assert call_kwargs["input"] == ["search query"]


# ---------------------------------------------------------------------------
# Mistral provider selection
# ---------------------------------------------------------------------------

class TestMistralSelection:
    def test_use_mistral_when_configured(self):
        from app.services import embedder
        from app.config import settings
        orig_provider = settings.EMBEDDING_PROVIDER
        orig_key = settings.MISTRAL_API_KEY
        try:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", "mistral")
            object.__setattr__(settings, "MISTRAL_API_KEY", "test-key")
            assert embedder._use_mistral()  # truthy when both provider=mistral and key set
        finally:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", orig_provider)
            object.__setattr__(settings, "MISTRAL_API_KEY", orig_key)

    def test_use_openai_by_default(self):
        from app.services import embedder
        from app.config import settings
        orig_provider = settings.EMBEDDING_PROVIDER
        orig_key = settings.MISTRAL_API_KEY
        try:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", "openai")
            object.__setattr__(settings, "MISTRAL_API_KEY", "")
            assert not embedder._use_mistral()
        finally:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", orig_provider)
            object.__setattr__(settings, "MISTRAL_API_KEY", orig_key)

    def test_use_openai_when_mistral_no_key(self):
        from app.services import embedder
        from app.config import settings
        orig_provider = settings.EMBEDDING_PROVIDER
        orig_key = settings.MISTRAL_API_KEY
        try:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", "mistral")
            object.__setattr__(settings, "MISTRAL_API_KEY", "")
            assert not embedder._use_mistral()
        finally:
            object.__setattr__(settings, "EMBEDDING_PROVIDER", orig_provider)
            object.__setattr__(settings, "MISTRAL_API_KEY", orig_key)
