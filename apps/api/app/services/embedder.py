"""Génération d'embeddings — OpenAI (défaut) avec fallback Mistral (hébergé EU).

Priorité de sélection :
1. Si EMBEDDING_PROVIDER=mistral → Mistral Embed (hébergé en France, RGPD natif)
2. Sinon → OpenAI text-embedding-3-small (défaut, meilleur rapport qualité/prix)

Mistral Embed est recommandé pour la conformité RGPD car les données restent en EU.
"""
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)

# ── Lazy client init ─────────────────────────────────────────────────────
_openai_client = None
_mistral_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _get_mistral():
    global _mistral_client
    if _mistral_client is None:
        try:
            from mistralai import Mistral
            _mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
        except ImportError:
            logger.warning("mistral_sdk_not_installed", hint="pip install mistralai")
            return None
    return _mistral_client


def _use_mistral() -> bool:
    """Détermine si on utilise Mistral pour les embeddings."""
    return (
        settings.EMBEDDING_PROVIDER == "mistral"
        and settings.MISTRAL_API_KEY
    )


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Embeddings via OpenAI text-embedding-3-small."""
    client = _get_openai()
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [
            item.embedding
            for item in sorted(response.data, key=lambda x: x.index)
        ]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def _embed_mistral(texts: list[str]) -> list[list[float]]:
    """Embeddings via Mistral Embed (hébergé EU — serveurs France)."""
    client = _get_mistral()
    if client is None:
        raise RuntimeError("Mistral SDK non installé. pip install mistralai")

    all_embeddings = []
    batch_size = 50  # Mistral batch limit

    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        response = client.embeddings.create(
            model=settings.MISTRAL_EMBEDDING_MODEL,
            inputs=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Génère des embeddings pour une liste de textes.

    Utilise Mistral (EU) si configuré, sinon OpenAI (défaut).
    Batché automatiquement pour respecter les limites API.
    """
    if not texts:
        return []

    if _use_mistral():
        logger.debug("using_mistral_embeddings", count=len(texts))
        return _embed_mistral(texts)

    return _embed_openai(texts)


def embed_query(query: str) -> list[float]:
    """Embedding pour une requête de recherche."""
    if _use_mistral():
        result = _embed_mistral([query])
        return result[0]

    client = _get_openai()
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=[query],
    )
    return response.data[0].embedding
