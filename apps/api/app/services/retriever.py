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
        # Utiliser un savepoint pour ne pas annuler le travail précédent en cas d'erreur
        nested = db.begin_nested()
        rows = db.execute(
            sql,
            {
                "project_id": project_id,
                "query_vec": json.dumps(query_embedding),
                "max_distance": max_distance,
                "top_k": top_k,
            },
        ).fetchall()
        nested.commit()
    except Exception as e:
        logger.warning(f"RAG: pgvector query failed ({e}), fallback texte brut")
        nested.rollback()
        return _fallback_text_chunks(db, project_id, top_k)

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


def _fallback_text_chunks(db: Session, project_id: str, top_k: int = 15) -> list[dict]:
    """Fallback quand pgvector n'est pas disponible : retourne les chunks bruts sans ranking."""
    sql = text("""
        SELECT c.id, c.content, c.page_start, c.page_end, c.chunk_index,
               d.original_name AS doc_name, d.doc_type
        FROM chunks c
        JOIN ao_documents d ON d.id = c.document_id
        WHERE c.project_id = :project_id
        ORDER BY d.doc_type, c.chunk_index
        LIMIT :top_k
    """)
    try:
        rows = db.execute(sql, {"project_id": project_id, "top_k": top_k}).fetchall()
    except Exception as e2:
        logger.error(f"RAG fallback failed: {e2}")
        db.rollback()
        return []

    logger.info(f"RAG fallback: {len(rows)} chunks retournés (sans vector ranking)")
    return [
        {
            "id": str(row.id),
            "content": row.content,
            "page_start": row.page_start,
            "page_end": row.page_end,
            "doc_name": row.doc_name,
            "doc_type": row.doc_type,
            "similarity": 0.75,  # Score fictif pour le fallback
        }
        for row in rows
    ]


def _bm25_search(
    db: Session,
    project_id: str,
    query: str,
    top_k: int = 15,
) -> list[dict]:
    """PostgreSQL full-text keyword search using French stemming.

    Uses plainto_tsquery for safe query parsing (no special syntax needed).
    Returns chunks ranked by ts_rank DESC.
    """
    sql = text("""
        SELECT
            c.id,
            c.content,
            c.document_id AS doc_id,
            ts_rank(to_tsvector('french', c.content), plainto_tsquery('french', :query)) AS rank
        FROM chunks c
        WHERE c.project_id = :project_id
          AND to_tsvector('french', c.content) @@ plainto_tsquery('french', :query)
        ORDER BY rank DESC
        LIMIT :top_k
    """)

    try:
        nested = db.begin_nested()
        rows = db.execute(
            sql,
            {"project_id": project_id, "query": query, "top_k": top_k},
        ).fetchall()
        nested.commit()
    except Exception as e:
        logger.warning(f"BM25 search failed ({e}), returning empty")
        nested.rollback()
        return []

    return [
        {
            "id": str(row.id),
            "content": row.content,
            "doc_id": str(row.doc_id),
            "bm25_rank": float(row.rank),
        }
        for row in rows
    ]


def retrieve_hybrid(
    db: Session,
    project_id: str,
    query: str,
    top_k: int = 10,
    use_expansion: bool = False,
) -> list[dict]:
    """Hybrid search combining vector similarity + BM25 keyword search.

    Uses Reciprocal Rank Fusion (RRF) to merge the two ranked lists:
        rrf_score = 1/(k + rank_vector) + 1/(k + rank_bm25)
    where k=60 (standard RRF constant).

    When use_expansion=True, expands the query with BTP synonyms and runs
    vector search for each variant, deduplicating by chunk ID (keeping highest
    similarity).

    Falls back to vector-only results when BM25 returns nothing.
    """
    RRF_K = 60
    fetch_k = 2 * top_k

    # --- Vector search (with optional query expansion) ---
    if use_expansion:
        variants = expand_query(query)
        per_variant_k = max(1, fetch_k // len(variants))
        merged: dict[str, dict] = {}
        for variant in variants:
            chunks = retrieve_relevant_chunks(db, project_id, variant, top_k=per_variant_k)
            for c in chunks:
                existing = merged.get(c["id"])
                if existing is None or c.get("similarity", 0.0) > existing.get("similarity", 0.0):
                    merged[c["id"]] = c
        vector_chunks = sorted(merged.values(), key=lambda x: x.get("similarity", 0.0), reverse=True)
        logger.info(
            f"Query expansion: {len(variants)} variants → {len(vector_chunks)} unique vector chunks"
        )
    else:
        vector_chunks = retrieve_relevant_chunks(db, project_id, query, top_k=fetch_k)

    # --- BM25 search ---
    bm25_chunks = _bm25_search(db, project_id, query, top_k=fetch_k)

    # Fallback: if BM25 returned nothing, use vector results directly
    if not bm25_chunks:
        logger.info("Hybrid search: BM25 returned no results, using vector-only")
        return [
            {
                "id": c["id"],
                "content": c["content"],
                "score": c.get("similarity", 0.0),
                "doc_id": c.get("doc_id", ""),
            }
            for c in vector_chunks[:top_k]
        ]

    # Build rank maps (chunk_id -> 1-based rank)
    vector_ranks: dict[str, int] = {}
    for rank, c in enumerate(vector_chunks, start=1):
        vector_ranks[c["id"]] = rank

    bm25_ranks: dict[str, int] = {}
    for rank, c in enumerate(bm25_chunks, start=1):
        bm25_ranks[c["id"]] = rank

    # Collect all unique chunk IDs and their content/doc_id
    all_chunks: dict[str, dict] = {}
    for c in vector_chunks:
        all_chunks[c["id"]] = {"content": c["content"], "doc_id": c.get("doc_id", "")}
    for c in bm25_chunks:
        if c["id"] not in all_chunks:
            all_chunks[c["id"]] = {"content": c["content"], "doc_id": c.get("doc_id", "")}

    # Compute RRF scores
    scored: list[dict] = []
    for chunk_id, info in all_chunks.items():
        v_rank = vector_ranks.get(chunk_id)
        b_rank = bm25_ranks.get(chunk_id)

        rrf_score = 0.0
        if v_rank is not None:
            rrf_score += 1.0 / (RRF_K + v_rank)
        if b_rank is not None:
            rrf_score += 1.0 / (RRF_K + b_rank)

        scored.append({
            "id": chunk_id,
            "content": info["content"],
            "score": round(rrf_score, 6),
            "doc_id": info["doc_id"],
        })

    # Sort by RRF score descending, take top_k
    scored.sort(key=lambda x: x["score"], reverse=True)

    logger.info(
        f"Hybrid search: {len(vector_chunks)} vector + {len(bm25_chunks)} BM25 "
        f"→ {min(top_k, len(scored))} merged results for project_id={project_id!r}"
    )

    return scored[:top_k]


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


# BTP synonym dictionary for query expansion
_BTP_SYNONYMS = {
    "sous-traitance": ["sous-traitant", "co-traitance", "groupement", "cotraitant"],
    "pénalités": ["pénalité de retard", "sanctions", "retenues", "malus"],
    "délai": ["délais", "durée", "planning", "calendrier", "échéance"],
    "garantie": ["garantie décennale", "garantie de parfait achèvement", "caution", "retenue de garantie"],
    "prix": ["montant", "coût", "tarif", "chiffrage", "devis", "BPU", "DPGF"],
    "assurance": ["RC professionnelle", "décennale", "police d'assurance", "attestation"],
    "qualification": ["certification", "Qualibat", "RGE", "habilitation", "compétence"],
    "travaux": ["chantier", "ouvrage", "construction", "rénovation", "réhabilitation"],
    "lot": ["allotissement", "lots séparés", "lot unique", "décomposition"],
    "visite": ["visite de site", "visite obligatoire", "reconnaissance des lieux"],
    "mémoire": ["mémoire technique", "note méthodologique", "offre technique"],
    "sécurité": ["PPSPS", "PGC", "coordonnateur SPS", "prévention", "CSPS"],
    "déchets": ["SOGED", "gestion des déchets", "tri sélectif", "valorisation"],
    "amiante": ["désamiantage", "SS3", "SS4", "diagnostic amiante", "DTA"],
    "révision": ["révision de prix", "actualisation", "indexation", "BT01", "TP01"],
    "avance": ["avance forfaitaire", "avance obligatoire", "acompte"],
    "réception": ["OPR", "levée de réserves", "réception des travaux", "PV de réception"],
}


def expand_query(query: str) -> list[str]:
    """Expand a RAG query with BTP-specific synonyms (rule-based, no LLM).

    Returns the original query plus up to 2 synonym-enriched variants.
    Used to improve recall on specialized BTP terminology.
    """
    query_lower = query.lower()
    variants = [query]

    matched_synonyms = []
    for term, synonyms in _BTP_SYNONYMS.items():
        if term in query_lower:
            matched_synonyms.extend(synonyms[:2])  # Max 2 synonyms per matched term

    if matched_synonyms:
        # Create variant 1: original + first batch of synonyms
        variant1 = query + " " + " ".join(matched_synonyms[:3])
        variants.append(variant1)

        # Create variant 2 if enough synonyms
        if len(matched_synonyms) > 3:
            variant2 = query + " " + " ".join(matched_synonyms[3:6])
            variants.append(variant2)

    return variants


def rerank_with_llm(
    chunks: list[dict],
    query: str,
    top_k: int = 10,
) -> list[dict]:
    """Rerank chunks using Claude for contextual relevance scoring.

    Only applied when >10 chunks and for complex queries (conflicts, checklist,
    questions). Each chunk gets a relevance score 1-10; chunks scoring < 5 are dropped.

    Uses minimal tokens (max_tokens=256) and benefits from prompt caching.
    """
    if len(chunks) <= top_k:
        return chunks

    from app.services.llm import llm_service

    # Build compact chunk list for reranking
    chunk_texts = []
    for i, c in enumerate(chunks):
        text_preview = c.get("content", "")[:200]
        chunk_texts.append(f"[{i}] {text_preview}")

    chunks_block = "\n".join(chunk_texts)

    system = (
        "Tu es un expert en pertinence documentaire pour marchés publics BTP. "
        "Score chaque chunk de 1 (non pertinent) à 10 (très pertinent) par rapport à la requête. "
        "Réponds UNIQUEMENT en JSON : {\"scores\": [score_0, score_1, ...]}"
    )
    user = f"Requête : {query}\n\nChunks :\n{chunks_block}"

    try:
        result = llm_service.complete_json(
            system_prompt=system,
            user_prompt=user,
        )
        scores = result.get("scores", [])
        if len(scores) != len(chunks):
            logger.warning("Reranking: score count mismatch, returning original order")
            return chunks[:top_k]

        # Pair chunks with scores, filter < 5, sort desc
        scored = [(chunks[i], s) for i, s in enumerate(scores) if s >= 5]
        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = [c for c, _ in scored[:top_k]]
        logger.info(f"Reranking: {len(chunks)} → {len(reranked)} chunks (query={query[:40]!r})")
        return reranked

    except Exception as e:
        logger.warning(f"Reranking failed ({e}), returning original order")
        return chunks[:top_k]
