"""RAG retrieval — numpy cosine similarity over JSONB embeddings.

Inclut un seuil de similarité minimum (SIMILARITY_THRESHOLD) pour éviter
les hallucinations quand le contexte RAG est pauvre.
"""
import logging
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embedder import embed_query

logger = logging.getLogger(__name__)

# Seuil minimum de similarité — en dessous, le chunk est considéré non pertinent
SIMILARITY_THRESHOLD = 0.35


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def retrieve_relevant_chunks(
    db: Session,
    project_id: str,
    query: str,
    top_k: int = 15,
    min_similarity: float = SIMILARITY_THRESHOLD,
) -> list[dict]:
    """Cosine similarity search with minimum threshold.

    Returns chunks sorted by similarity DESC, filtered by min_similarity.
    Each chunk includes a 'similarity' field for downstream confidence scoring.
    """
    query_embedding = embed_query(query)

    sql = text("""
        SELECT
            c.id,
            c.content,
            c.page_start,
            c.page_end,
            c.chunk_index,
            c.embedding,
            d.original_name AS doc_name,
            d.doc_type
        FROM chunks c
        JOIN ao_documents d ON d.id = c.document_id
        WHERE c.project_id = :project_id
          AND c.embedding IS NOT NULL
    """)

    rows = db.execute(sql, {"project_id": project_id}).fetchall()

    if not rows:
        logger.debug(f"RAG: 0 chunks with embeddings for project_id={project_id!r}")
        return []

    # Compute cosine similarity in Python
    scored = []
    for row in rows:
        emb = row.embedding
        if not emb:
            continue
        sim = _cosine_similarity(query_embedding, emb)
        # Filtrer par seuil minimum de similarité
        if sim >= min_similarity:
            scored.append((sim, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    total_above_threshold = len(scored)
    logger.debug(
        f"RAG: {len(top)}/{total_above_threshold} chunks selected "
        f"(threshold={min_similarity}, total_embeddings={len(rows)}) "
        f"for project_id={project_id!r}"
    )

    if not top:
        logger.warning(
            f"RAG: Aucun chunk au-dessus du seuil {min_similarity} "
            f"pour project_id={project_id!r} (query={query[:60]!r})"
        )

    return [
        {
            "id": str(row.id),
            "content": row.content,
            "page_start": row.page_start,
            "page_end": row.page_end,
            "doc_name": row.doc_name,
            "doc_type": row.doc_type,
            "similarity": float(sim),
        }
        for sim, row in top
    ]


def format_context(chunks: list[dict]) -> str:
    """Formate les chunks récupérés en contexte pour le LLM."""
    if not chunks:
        return "(Aucun contexte disponible — les documents ne contiennent pas d'information pertinente pour cette requête)"
    parts = []
    for chunk in chunks:
        header = f"[{chunk['doc_name']} | p.{chunk['page_start']}–{chunk['page_end']}]"
        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def get_max_similarity(chunks: list[dict]) -> float:
    """Retourne la similarité maximale parmi les chunks."""
    if not chunks:
        return 0.0
    return max(c.get("similarity", 0.0) for c in chunks)
