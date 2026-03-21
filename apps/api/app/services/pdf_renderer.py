"""Abstraction de rendu PDF — xhtml2pdf (défaut) ou WeasyPrint (optionnel).

WeasyPrint offre un meilleur support CSS3 (flexbox, grid, @page avancé, SVG natif)
mais nécessite des dépendances système (Pango, GLib). Activable via feature flag.

Usage:
    from app.services.pdf_renderer import get_renderer
    renderer = get_renderer()
    pdf_bytes = renderer.render(html_content)
"""
import structlog
from abc import ABC, abstractmethod
from io import BytesIO

from app.config import settings

logger = structlog.get_logger(__name__)


class PDFRenderer(ABC):
    """Interface abstraite pour le rendu HTML → PDF."""

    @abstractmethod
    def render(self, html: str, base_url: str | None = None) -> bytes:
        """Convertit une string HTML en bytes PDF."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du renderer pour les logs."""
        ...


class XHtml2PDFRenderer(PDFRenderer):
    """Renderer xhtml2pdf — léger, sans dépendance système, CSS2.1 + partiel CSS3."""

    @property
    def name(self) -> str:
        return "xhtml2pdf"

    def render(self, html: str, base_url: str | None = None) -> bytes:
        from xhtml2pdf import pisa
        output = BytesIO()
        result = pisa.CreatePDF(html, dest=output, encoding="utf-8")
        if result.err:
            logger.warning("xhtml2pdf_warnings", count=result.err)
        return output.getvalue()


class WeasyPrintRenderer(PDFRenderer):
    """Renderer WeasyPrint — CSS3 complet, @page avancé, SVG natif.

    Nécessite weasyprint>=62.0 et ses dépendances système (Pango, GLib).
    Installable sur Linux/macOS ; Windows nécessite GTK.
    """

    @property
    def name(self) -> str:
        return "weasyprint"

    def render(self, html: str, base_url: str | None = None) -> bytes:
        try:
            import weasyprint
        except ImportError:
            logger.error("weasyprint_not_installed",
                         hint="pip install weasyprint>=62.0 (+ dépendances système)")
            raise RuntimeError(
                "WeasyPrint non installé. Installez weasyprint>=62.0 "
                "ou désactivez USE_WEASYPRINT dans la configuration."
            )

        doc = weasyprint.HTML(string=html, base_url=base_url)
        return doc.write_pdf()


def get_renderer(use_weasyprint: bool | None = None) -> PDFRenderer:
    """Factory pour obtenir le renderer PDF approprié.

    Args:
        use_weasyprint: Force le choix. Si None, utilise le setting USE_WEASYPRINT.

    Returns:
        Instance de PDFRenderer (xhtml2pdf ou WeasyPrint).
    """
    should_use_weasyprint = use_weasyprint if use_weasyprint is not None else getattr(
        settings, "USE_WEASYPRINT", False
    )

    if should_use_weasyprint:
        try:
            import weasyprint  # noqa: F401
            logger.debug("pdf_renderer_selected", renderer="weasyprint")
            return WeasyPrintRenderer()
        except ImportError:
            logger.warning("weasyprint_unavailable_fallback_xhtml2pdf")
            return XHtml2PDFRenderer()

    return XHtml2PDFRenderer()
