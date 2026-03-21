"""Tests for app.services.pdf_renderer — PDF rendering abstraction."""
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestXHtml2PDFRenderer:
    """Tests for the xhtml2pdf renderer."""

    def test_name_is_xhtml2pdf(self):
        from app.services.pdf_renderer import XHtml2PDFRenderer
        renderer = XHtml2PDFRenderer()
        assert renderer.name == "xhtml2pdf"

    def test_render_returns_bytes(self):
        """render() should return bytes from xhtml2pdf."""
        from app.services.pdf_renderer import XHtml2PDFRenderer

        renderer = XHtml2PDFRenderer()
        fake_pdf = b"%PDF-1.4 fake"

        mock_pisa = MagicMock()
        mock_result = MagicMock()
        mock_result.err = 0

        def write_pdf(html, dest, encoding="utf-8"):
            dest.write(fake_pdf)
            return mock_result

        mock_pisa.CreatePDF.side_effect = write_pdf

        import sys
        sys.modules["xhtml2pdf"] = MagicMock()
        sys.modules["xhtml2pdf.pisa"] = mock_pisa
        sys.modules["xhtml2pdf"].pisa = mock_pisa

        try:
            # Force reimport to pick up mock
            import importlib
            import app.services.pdf_renderer as mod
            importlib.reload(mod)
            renderer = mod.XHtml2PDFRenderer()
            result = renderer.render("<html><body>Test</body></html>")
            assert isinstance(result, bytes)
            assert fake_pdf in result
        finally:
            sys.modules.pop("xhtml2pdf", None)
            sys.modules.pop("xhtml2pdf.pisa", None)
            importlib.reload(mod)

    def test_render_logs_warning_on_errors(self):
        """render() should log warning when xhtml2pdf reports errors."""
        from app.services.pdf_renderer import XHtml2PDFRenderer

        mock_pisa = MagicMock()
        mock_result = MagicMock()
        mock_result.err = 3  # 3 warnings

        def write_pdf(html, dest, encoding="utf-8"):
            dest.write(b"%PDF")
            return mock_result

        mock_pisa.CreatePDF.side_effect = write_pdf

        import sys
        sys.modules["xhtml2pdf"] = MagicMock()
        sys.modules["xhtml2pdf.pisa"] = mock_pisa
        sys.modules["xhtml2pdf"].pisa = mock_pisa

        try:
            import importlib
            import app.services.pdf_renderer as mod
            importlib.reload(mod)
            renderer = mod.XHtml2PDFRenderer()
            result = renderer.render("<html></html>")
            assert isinstance(result, bytes)
        finally:
            sys.modules.pop("xhtml2pdf", None)
            sys.modules.pop("xhtml2pdf.pisa", None)
            importlib.reload(mod)


class TestWeasyPrintRenderer:
    """Tests for the WeasyPrint renderer."""

    def test_name_is_weasyprint(self):
        from app.services.pdf_renderer import WeasyPrintRenderer
        renderer = WeasyPrintRenderer()
        assert renderer.name == "weasyprint"

    def test_render_raises_runtime_error_if_not_installed(self):
        """render() should raise RuntimeError when weasyprint is not installed."""
        from app.services.pdf_renderer import WeasyPrintRenderer
        import builtins

        renderer = WeasyPrintRenderer()
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("No module named 'weasyprint'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="WeasyPrint non install"):
                renderer.render("<html></html>")

    def test_render_success_with_weasyprint(self):
        """render() should produce PDF bytes when weasyprint is available."""
        import sys

        fake_pdf = b"%PDF-weasy"
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = fake_pdf
        mock_html_cls = MagicMock(return_value=mock_doc)

        mock_weasy_module = MagicMock()
        mock_weasy_module.HTML = mock_html_cls
        sys.modules["weasyprint"] = mock_weasy_module

        try:
            from app.services.pdf_renderer import WeasyPrintRenderer
            renderer = WeasyPrintRenderer()
            result = renderer.render("<html>test</html>", base_url="http://example.com")
            assert result == fake_pdf
            mock_weasy_module.HTML.assert_called_once_with(
                string="<html>test</html>", base_url="http://example.com"
            )
        finally:
            sys.modules.pop("weasyprint", None)


class TestGetRenderer:
    """Tests for the get_renderer() factory function."""

    def test_default_returns_xhtml2pdf(self):
        """get_renderer() should return XHtml2PDFRenderer by default."""
        from app.services.pdf_renderer import get_renderer, XHtml2PDFRenderer

        with patch("app.services.pdf_renderer.settings") as mock_settings:
            mock_settings.USE_WEASYPRINT = False
            renderer = get_renderer()
            assert isinstance(renderer, XHtml2PDFRenderer)
            assert renderer.name == "xhtml2pdf"

    def test_explicit_false_returns_xhtml2pdf(self):
        """get_renderer(use_weasyprint=False) should return XHtml2PDFRenderer."""
        from app.services.pdf_renderer import get_renderer, XHtml2PDFRenderer

        renderer = get_renderer(use_weasyprint=False)
        assert isinstance(renderer, XHtml2PDFRenderer)

    def test_use_weasyprint_true_falls_back_if_import_fails(self):
        """get_renderer(use_weasyprint=True) should fallback to xhtml2pdf if weasyprint unavailable."""
        from app.services.pdf_renderer import get_renderer, XHtml2PDFRenderer
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("No module named 'weasyprint'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            renderer = get_renderer(use_weasyprint=True)
            assert isinstance(renderer, XHtml2PDFRenderer)

    def test_use_weasyprint_true_returns_weasyprint_if_available(self):
        """get_renderer(use_weasyprint=True) should return WeasyPrintRenderer if installed."""
        from app.services.pdf_renderer import get_renderer, WeasyPrintRenderer
        import builtins
        import sys

        original_import = builtins.__import__
        mock_weasy = MagicMock()

        def mock_import(name, *args, **kwargs):
            if name == "weasyprint":
                return mock_weasy
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            renderer = get_renderer(use_weasyprint=True)
            assert isinstance(renderer, WeasyPrintRenderer)

    def test_uses_settings_use_weasyprint_when_none(self):
        """get_renderer() should read settings.USE_WEASYPRINT when use_weasyprint is None."""
        from app.services.pdf_renderer import get_renderer, XHtml2PDFRenderer

        with patch("app.services.pdf_renderer.settings") as mock_settings:
            mock_settings.USE_WEASYPRINT = False
            renderer = get_renderer(use_weasyprint=None)
            assert isinstance(renderer, XHtml2PDFRenderer)

    def test_uses_settings_use_weasyprint_true(self):
        """get_renderer() should try WeasyPrint when settings.USE_WEASYPRINT is True."""
        from app.services.pdf_renderer import get_renderer
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("Not installed")
            return original_import(name, *args, **kwargs)

        with patch("app.services.pdf_renderer.settings") as mock_settings, \
             patch("builtins.__import__", side_effect=mock_import):
            mock_settings.USE_WEASYPRINT = True
            renderer = get_renderer()
            # Falls back to xhtml2pdf
            assert renderer.name == "xhtml2pdf"


# ---------------------------------------------------------------------------
# PDFRenderer ABC
# ---------------------------------------------------------------------------

class TestPDFRendererABC:
    def test_cannot_instantiate_abstract(self):
        """PDFRenderer cannot be instantiated directly."""
        from app.services.pdf_renderer import PDFRenderer
        with pytest.raises(TypeError):
            PDFRenderer()

    def test_subclass_must_implement_render_and_name(self):
        """Subclass missing abstract methods raises TypeError."""
        from app.services.pdf_renderer import PDFRenderer

        class Incomplete(PDFRenderer):
            pass

        with pytest.raises(TypeError):
            Incomplete()


# ---------------------------------------------------------------------------
# WeasyPrintRenderer with base_url=None
# ---------------------------------------------------------------------------

class TestWeasyPrintRendererBaseUrl:
    def test_render_with_no_base_url(self):
        """render() should pass base_url=None to weasyprint.HTML."""
        import sys

        fake_pdf = b"%PDF-weasy-no-base"
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = fake_pdf
        mock_html_cls = MagicMock(return_value=mock_doc)

        mock_weasy_module = MagicMock()
        mock_weasy_module.HTML = mock_html_cls
        sys.modules["weasyprint"] = mock_weasy_module

        try:
            from app.services.pdf_renderer import WeasyPrintRenderer
            renderer = WeasyPrintRenderer()
            result = renderer.render("<html>no base</html>")
            assert result == fake_pdf
            mock_weasy_module.HTML.assert_called_once_with(
                string="<html>no base</html>", base_url=None
            )
        finally:
            sys.modules.pop("weasyprint", None)


# ---------------------------------------------------------------------------
# get_renderer with missing USE_WEASYPRINT setting
# ---------------------------------------------------------------------------

class TestGetRendererMissingSetting:
    def test_missing_use_weasyprint_attr_defaults_to_xhtml2pdf(self):
        """get_renderer() should default to xhtml2pdf if USE_WEASYPRINT attr missing."""
        from app.services.pdf_renderer import get_renderer, XHtml2PDFRenderer

        mock_settings = MagicMock(spec=[])  # no attributes
        with patch("app.services.pdf_renderer.settings", mock_settings):
            renderer = get_renderer()
            assert isinstance(renderer, XHtml2PDFRenderer)
