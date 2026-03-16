"""RAG retrieval — pgvector cosine distance for fast similarity search.

Utilise l'opérateur pgvector <=> (cosine distance) pour une recherche
vectorielle performante côté SQL, au lieu du calcul numpy côté Python.
Inclut un seuil de similarité minimum (SIMILARITY_THRESHOLD) pour éviter
les hallucinations quand le contexte RAG est pauvre.
"""
import json
import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embedder import embed_query

logger = structlog.get_logger(__name__)

# Seuil minimum de similarité — en dessous, le chunk est considéré non pertinent
# 0.50 = plus strict que 0.35, réduit les hallucinations sur DCE mal structurés/OCR
SIMILARITY_THRESHOLD = 0.50


def retrieve_relevant_chunks(
    db: Session,
    project_id: str,
    query: str,
    top_k: int = 15,
    min_similarity: float = SIMILARITY_THRESHOLD,
) -> list[dict]:
    """pgvector cosine similarity search with minimum threshold.

    Uses the <=> operator (cosine distance) for server-side vector search.
    cosine_distance = 1 - cosine_similarity, so we filter where distance < (1 - min_similarity).

    Returns chunks sorted by similarity DESC, filtered by min_similarity.
    Each chunk includes a 'similarity' field for downstream confidence scoring.
    """
    # Vérification rapide : pas de chunks → retourner vide sans appel API embedding
    count_row = db.execute(
        text("SELECT COUNT(*) FROM chunks WHERE project_id = :pid AND embedding IS NOT NULL"),
        {"pid": project_id},
    ).fetchone()
    if not count_row or count_row[0] == 0:
        logger.warning(f"RAG: Aucun chunk pour project_id={project_id!r}, contexte vide")
        return []

    query_embedding = embed_query(query)
    max_distance = 1.0 - min_similarity  # cosine distance threshold

    sql = text("""
        SELECT
            c.id,
            c.content,
            c.page_start,
            c.page_end,
            c.chunk_index,
            d.original_name AS doc_name,
            d.doc_type,
            (c.embedding <=> CAST(:query_vec AS vector)) AS distance
        FROM chunks c
        JOIN ao_documents d ON d.id = c.document_id
        WHERE c.project_id = :project_id
          AND c.embedding IS NOT NULL
          AND (c.embedding <=> CAST(:query_vec AS vector)) < :max_distance
        ORDER BY distance ASC
        LIMIT :top_k
    """)

    try:
        rows = db.execute(
            sql,
            {
                "project_id": project_id,
                "query_vec": json.dumps(query_embedding),
                "max_distance": max_distance,
                "top_k": top_k,
            },
        ).fetchall()
    except Exception as e:
        logger.warning(f"RAG: pgvector query failed ({e}), contexte vide")
        db.rollback()
        return []

    if not rows:
        logger.warning(
            f"RAG: Aucun chunk au-dessus du seuil {min_similarity} "
            f"pour project_id={project_id!r} (query={query[:60]!r})"
        )
        return []

    logger.debug(
        f"RAG: {len(rows)} chunks selected via pgvector "
        f"(threshold={min_similarity}, max_distance={max_distance:.3f}) "
        f"for project_id={project_id!r}"
    )

    return [
        {
            "id": str(row.id),
            "content": row.content,
            "page_start": row.page_start,
            "page_end": row.page_end,
            "doc_name": row.doc_name,
            "doc_type": row.doc_type,
            "similarity": round(1.0 - float(row.distance), 4),
        }
        for row in rows
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
