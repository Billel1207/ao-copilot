"""Découpage du texte en chunks pour RAG."""
import re
from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

CHUNK_SIZE = 800       # tokens
CHUNK_OVERLAP = 150    # tokens

# Structural markers for article-level chunking (CCAP, CCTP, RC, AE)
STRUCTURE_PATTERN = re.compile(
    r'^(Article|Chapitre|Section|TITRE|PARTIE)\s+[\dIVXLCM]+[.\s\-\u2013:]|'
    r'^\d+\.\d+[\.\s]',
    re.MULTILINE | re.IGNORECASE
)

# Document types that benefit from structure-aware chunking
STRUCTURED_DOC_TYPES = {"ccap", "cctp", "rc", "ae"}


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_start: int
    page_end: int
    token_count: int
    context_prefix: str = ""


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


def build_page_text(pages: list[dict]) -> list[tuple[int, str]]:
    """Retourne [(page_num, text), ...]."""
    return [(p["page_num"], p["raw_text"] or "") for p in pages if p.get("raw_text")]


def contextualize_chunk(content: str, doc_type: str, doc_name: str, section_header: str = "") -> str:
    """Prepend document context to chunk for better retrieval precision.

    A chunk like 'le delai est de 30 jours' becomes:
    '[CCAP: Renovation gymnase, Article 5 - Delais] le delai est de 30 jours...'
    This resolves ambiguity between RC delays vs CCAP execution delays.
    """
    parts = [f"[{doc_type}"]
    if doc_name:
        # Clean extension from name
        clean_name = doc_name.rsplit(".", 1)[0] if "." in doc_name else doc_name
        parts.append(f": {clean_name}")
    if section_header:
        parts.append(f", {section_header}")
    parts.append("] ")
    prefix = "".join(parts)
    return prefix + content


def _find_page_range(pos: int, end_pos: int, page_positions: list[tuple[int, int, int]]) -> tuple[int, int]:
    """Determine page_start and page_end for a text span."""
    pages_covered = [
        pn for pn, ps, pe in page_positions
        if not (pe <= pos or ps >= end_pos)
    ]
    page_start = min(pages_covered) if pages_covered else 1
    page_end = max(pages_covered) if pages_covered else 1
    return page_start, page_end


def chunk_by_structure(
    full_text: str,
    page_positions: list[tuple[int, int, int]],
    doc_type: str = "",
    doc_name: str = "",
) -> list[TextChunk]:
    """Split text by structural markers (Article, Chapitre, Section, etc.).

    Falls back to RecursiveCharacterTextSplitter for sections exceeding 1200 tokens.
    Merges very short sections (<50 tokens) with the next section.
    """
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    # Find all structural boundaries
    matches = list(STRUCTURE_PATTERN.finditer(full_text))

    if not matches:
        # No structure found — fall back to fixed-size chunking
        return _fixed_size_chunks(full_text, page_positions, doc_type, doc_name)

    # Build sections: list of (header, start_pos, end_pos)
    sections: list[tuple[str, int, int]] = []

    # Text before first match (preamble)
    if matches[0].start() > 0:
        sections.append(("", 0, matches[0].start()))

    for i, m in enumerate(matches):
        header = m.group(0).strip().rstrip(":").rstrip("-").rstrip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        sections.append((header, start, end))

    # Merge very short sections (<50 tokens) with next section
    merged: list[tuple[str, int, int]] = []
    i = 0
    while i < len(sections):
        header, start, end = sections[i]
        section_text = full_text[start:end]
        if count_tokens(section_text) < 50 and i + 1 < len(sections):
            # Merge with next section
            next_header, _, next_end = sections[i + 1]
            combined_header = header if header else next_header
            merged.append((combined_header, start, next_end))
            i += 2
        else:
            merged.append((header, start, end))
            i += 1

    # Build chunks from merged sections
    chunks: list[TextChunk] = []
    chunk_idx = 0
    max_section_tokens = 1200

    for header, start, end in merged:
        section_text = full_text[start:end]
        token_count = count_tokens(section_text)

        if token_count > max_section_tokens:
            # Section too large — sub-split with RecursiveCharacterTextSplitter
            sub_chunks = fallback_splitter.split_text(section_text)
            sub_offset = start
            for sub_text in sub_chunks:
                sub_pos = full_text.find(sub_text, sub_offset)
                if sub_pos == -1:
                    sub_pos = sub_offset
                sub_end = sub_pos + len(sub_text)

                page_start, page_end = _find_page_range(sub_pos, sub_end, page_positions)
                prefix = ""
                if doc_type:
                    contextualized = contextualize_chunk(sub_text, doc_type, doc_name, header)
                    prefix = contextualized[: len(contextualized) - len(sub_text)]
                    sub_text = contextualized

                tc = count_tokens(sub_text)
                chunks.append(TextChunk(
                    content=sub_text,
                    chunk_index=chunk_idx,
                    page_start=page_start,
                    page_end=page_end,
                    token_count=tc,
                    context_prefix=prefix,
                ))
                chunk_idx += 1
                sub_offset = sub_pos + 1
        else:
            page_start, page_end = _find_page_range(start, end, page_positions)
            prefix = ""
            content = section_text
            if doc_type:
                contextualized = contextualize_chunk(section_text, doc_type, doc_name, header)
                prefix = contextualized[: len(contextualized) - len(section_text)]
                content = contextualized

            tc = count_tokens(content)
            chunks.append(TextChunk(
                content=content,
                chunk_index=chunk_idx,
                page_start=page_start,
                page_end=page_end,
                token_count=tc,
                context_prefix=prefix,
            ))
            chunk_idx += 1

    return chunks


def _fixed_size_chunks(
    full_text: str,
    page_positions: list[tuple[int, int, int]],
    doc_type: str = "",
    doc_name: str = "",
) -> list[TextChunk]:
    """Standard fixed-size chunking with optional contextual prefix."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    raw_chunks = splitter.split_text(full_text)
    chunks: list[TextChunk] = []

    offset = 0
    for idx, chunk_text in enumerate(raw_chunks):
        pos = full_text.find(chunk_text, offset)
        if pos == -1:
            pos = offset
        end_pos = pos + len(chunk_text)

        page_start, page_end = _find_page_range(pos, end_pos, page_positions)

        prefix = ""
        content = chunk_text
        if doc_type:
            contextualized = contextualize_chunk(chunk_text, doc_type, doc_name)
            prefix = contextualized[: len(contextualized) - len(chunk_text)]
            content = contextualized

        tokens = count_tokens(content)
        chunks.append(TextChunk(
            content=content,
            chunk_index=idx,
            page_start=page_start,
            page_end=page_end,
            token_count=tokens,
            context_prefix=prefix,
        ))
        offset = pos + 1

    return chunks


def chunk_pages(pages: list[dict], doc_name: str = "", doc_type: str = "") -> list[TextChunk]:
    """
    pages : [{"page_num": int, "raw_text": str}, ...]
    Retourne une liste de TextChunk avec mapping de pages.

    doc_type : type de document (ccap, cctp, rc, ae, dpgf, bpu, etc.)
               Pour les types structurés (ccap, cctp, rc, ae), utilise
               le découpage par structure (articles/chapitres).
    """
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

    # Use structure-aware chunking for legal/structured documents
    if doc_type.lower() in STRUCTURED_DOC_TYPES:
        return chunk_by_structure(full_text, page_positions, doc_type, doc_name)

    # Default: fixed-size chunking
    return _fixed_size_chunks(full_text, page_positions, doc_type, doc_name)
