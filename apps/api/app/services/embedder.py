"""Génération d'embeddings via OpenAI text-embedding-3-small (vecteurs uniquement)."""
from openai import OpenAI
from app.config import settings

# Client OpenAI dédié aux embeddings (l'analyse IA utilise Claude/Anthropic)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Génère des embeddings pour une liste de textes.
    Batché par 100 pour respecter les limites API.
    """
    if not texts:
        return []

    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        response = _client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [
            item.embedding
            for item in sorted(response.data, key=lambda x: x.index)
        ]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embedding pour une requête de recherche."""
    response = _client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=[query],
    )
    return response.data[0].embedding
