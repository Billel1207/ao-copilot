"""Extraction texte multi-format : PDF, images (JPEG/PNG/TIFF), Word (.docx)."""
from dataclasses import dataclass
from pathlib import Path
import re
import fitz  # PyMuPDF
import pytesseract
import structlog
from PIL import Image
import io

logger = structlog.get_logger(__name__)

# Marqueur inséré dans le texte si l'OCR échoue — permet à l'analyse IA
# de détecter que cette page n'a pas été extraite correctement.
OCR_FAILURE_MARKER = "[TEXTE_NON_EXTRACTIBLE]"


@dataclass
class PageResult:
    page_num: int
    raw_text: str
    char_count: int
    section: str | None
    needs_ocr: bool


SECTION_PATTERNS = [
    (r"(?i)^\s*(article\s+\d+|chapitre\s+\d+|section\s+\d+)", "section"),
    (r"(?i)^(RC|règlement de consultation)", "RC"),
    (r"(?i)^(CCTP|cahier des clauses techniques)", "CCTP"),
    (r"(?i)^(CCAP|cahier des clauses administratives)", "CCAP"),
    (r"(?i)^(DPGF|décomposition du prix)", "DPGF"),
    (r"(?i)^(BPU|bordereau des prix)", "BPU"),
    (r"(?i)^(acte d'engagement|acte engagement)", "AE"),
]

OCR_THRESHOLD = 50  # chars/page sous lesquels on déclenche l'OCR


def detect_section(text: str) -> str | None:
    for pattern, label in SECTION_PATTERNS:
        if re.search(pattern, text[:200]):
            return label
    return None


def extract_pages(pdf_bytes: bytes) -> list[PageResult]:
    """Extrait le texte page par page depuis un PDF."""
    results: list[PageResult] = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Impossible d'ouvrir le PDF : {e}")

    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text("text")
        char_count = len(raw_text.strip())
        needs_ocr = char_count < OCR_THRESHOLD

        if needs_ocr:
            raw_text = _ocr_page(page)
            char_count = len(raw_text.strip())

        section = detect_section(raw_text)

        results.append(PageResult(
            page_num=page_num + 1,
            raw_text=raw_text.strip(),
            char_count=char_count,
            section=section,
            needs_ocr=needs_ocr,
        ))

    doc.close()
    return results


def _ocr_page(page: fitz.Page) -> str:
    """OCR via Tesseract sur une page PDF scannée.

    Retourne OCR_FAILURE_MARKER si Tesseract est indisponible ou échoue,
    pour permettre la détection du problème en aval.
    """
    try:
        mat = fitz.Matrix(2.0, 2.0)  # zoom x2 pour meilleure qualité OCR
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image, lang="fra+eng")
        return text
    except Exception as exc:
        logger.warning(
            "ocr_page_failed",
            page_num=getattr(page, "number", "?"),
            error=str(exc),
            hint="Vérifiez que Tesseract est installé et que tesseract-ocr-fra est disponible",
        )
        return OCR_FAILURE_MARKER


def has_sufficient_text(pages: list[PageResult], threshold: float = 0.3) -> bool:
    """Vérifie si au moins 30% des pages ont du texte suffisant."""
    if not pages:
        return False
    ok = sum(1 for p in pages if p.char_count >= OCR_THRESHOLD)
    return (ok / len(pages)) >= threshold


def clean_text(text: str) -> str:
    """Nettoyage basique : suppression répétitions headers/footers."""
    lines = text.split("\n")
    # Supprimer lignes très courtes répétitives (headers/footers)
    cleaned = [line for line in lines if len(line.strip()) > 3]
    return "\n".join(cleaned)


# ── Extracteurs multi-format ─────────────────────────────────────────────────

def extract_image_file(image_bytes: bytes, filename: str) -> list[PageResult]:
    """Extrait le texte d'une image (JPEG, PNG, TIFF) via OCR Tesseract."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="fra+eng")
        text = text.strip() or OCR_FAILURE_MARKER
        return [PageResult(
            page_num=1,
            raw_text=text,
            char_count=len(text),
            section=detect_section(text),
            needs_ocr=True,
        )]
    except Exception as exc:
        logger.warning("image_extraction_failed", filename=filename, error=str(exc))
        return [PageResult(page_num=1, raw_text=OCR_FAILURE_MARKER, char_count=0, section=None, needs_ocr=True)]


def extract_docx_file(docx_bytes: bytes) -> list[PageResult]:
    """Extrait le texte d'un document Word (.docx) via python-docx."""
    try:
        from docx import Document  # python-docx
        doc = Document(io.BytesIO(docx_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Inclure aussi les tableaux
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())
        full_text = "\n".join(paragraphs) or OCR_FAILURE_MARKER
        return [PageResult(
            page_num=1,
            raw_text=full_text,
            char_count=len(full_text),
            section=detect_section(full_text),
            needs_ocr=False,
        )]
    except Exception as exc:
        logger.warning("docx_extraction_failed", error=str(exc))
        return [PageResult(page_num=1, raw_text=OCR_FAILURE_MARKER, char_count=0, section=None, needs_ocr=False)]


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


def extract_document(file_bytes: bytes, filename: str) -> list[PageResult]:
    """Dispatch vers le bon extracteur selon l'extension du fichier."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_pages(file_bytes)
    elif ext in IMAGE_EXTENSIONS:
        return extract_image_file(file_bytes, filename)
    elif ext == ".docx":
        return extract_docx_file(file_bytes)
    else:
        raise ValueError(f"Format non supporté : {ext}")
