"""Découpage du texte en chunks pour RAG."""
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

CHUNK_SIZE = 800       # tokens
CHUNK_OVERLAP = 150    # tokens


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_start: int
    page_end: int
    token_count: int


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


def build_page_text(pages: list[dict]) -> list[tuple[int, str]]:
    """Retourne [(page_num, text), ...]."""
    return [(p["page_num"], p["raw_text"] or "") for p in pages if p.get("raw_text")]


def chunk_pages(pages: list[dict], doc_name: str = "") -> list[TextChunk]:
    """
    pages : [{"page_num": int, "raw_text": str}, ...]
    Retourne une liste de TextChunk avec mapping de pages.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,  # approximation chars (1 token ≈ 4 chars)
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    # Construire un texte annoté avec marqueurs de pages
    full_text = ""
    page_positions: list[tuple[int, int, int]] = []  # (page_num, start_pos, end_pos)

    for page_num, text in build_page_text(pages):
        start = len(full_text)
        full_text += text + "\n"
        end = len(full_text)
        page_positions.append((page_num, start, end))

    if not full_text.strip():
        return []

    raw_chunks = splitter.split_text(full_text)
    chunks: list[TextChunk] = []

    offset = 0
    for idx, chunk_text in enumerate(raw_chunks):
        # Trouver la position dans le texte complet
        pos = full_text.find(chunk_text, offset)
        if pos == -1:
            pos = offset
        end_pos = pos + len(chunk_text)

        # Détecter les pages couvertes
        pages_covered = [
            pn for pn, ps, pe in page_positions
            if not (pe <= pos or ps >= end_pos)
        ]
        page_start = min(pages_covered) if pages_covered else 1
        page_end = max(pages_covered) if pages_covered else 1

        tokens = count_tokens(chunk_text)
        chunks.append(TextChunk(
            content=chunk_text,
            chunk_index=idx,
            page_start=page_start,
            page_end=page_end,
            token_count=tokens,
        ))
        offset = pos + 1

    return chunks
