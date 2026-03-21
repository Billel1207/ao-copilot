"""Tests pour app/services/exporter.py — template loading, helpers, and re-exports."""
import os
import base64
import pytest
from unittest.mock import patch, MagicMock


class TestExporterTemplate:
    def test_export_template_loaded_and_contains_html(self):
        from app.services.exporter import EXPORT_TEMPLATE
        assert isinstance(EXPORT_TEMPLATE, str)
        assert len(EXPORT_TEMPLATE) > 100
        lower = EXPORT_TEMPLATE.lower()
        assert "<!doctype" in lower or "<html" in lower

    def test_template_file_exists_on_disk(self):
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "templates", "export_template.html"
        )
        assert os.path.isfile(template_path), f"Template not found at {template_path}"


class TestExporterReExports:
    def test_generate_export_docx_importable(self):
        from app.services.exporter import generate_export_docx
        assert callable(generate_export_docx)

    def test_generate_memo_technique_importable(self):
        from app.services.exporter import generate_memo_technique
        assert callable(generate_memo_technique)


# ---------------------------------------------------------------------------
# _format_date_fr
# ---------------------------------------------------------------------------

class TestFormatDateFr:
    def test_iso_date_only(self):
        from app.services.exporter import _format_date_fr
        assert _format_date_fr("2026-04-15") == "15/04/2026"

    def test_iso_datetime_with_T(self):
        from app.services.exporter import _format_date_fr
        result = _format_date_fr("2026-04-15T14:30:00")
        assert result == "15/04/2026 à 14h30"

    def test_iso_datetime_with_Z(self):
        from app.services.exporter import _format_date_fr
        result = _format_date_fr("2026-04-15T09:00:00Z")
        assert "15/04/2026" in result
        assert "09h00" in result

    def test_none_returns_empty_string(self):
        from app.services.exporter import _format_date_fr
        assert _format_date_fr(None) == ""

    def test_empty_string_returns_empty(self):
        from app.services.exporter import _format_date_fr
        assert _format_date_fr("") == ""

    def test_non_string_returns_value(self):
        from app.services.exporter import _format_date_fr
        assert _format_date_fr(12345) == 12345

    def test_invalid_date_returns_string(self):
        from app.services.exporter import _format_date_fr
        assert _format_date_fr("not-a-date") == "not-a-date"


# ---------------------------------------------------------------------------
# _safe_truncate
# ---------------------------------------------------------------------------

class TestSafeTruncate:
    def test_none_returns_empty(self):
        from app.services.exporter import _safe_truncate
        assert _safe_truncate(None) == ""

    def test_short_string_unchanged(self):
        from app.services.exporter import _safe_truncate
        assert _safe_truncate("hello", length=100) == "hello"

    def test_long_string_truncated(self):
        from app.services.exporter import _safe_truncate
        result = _safe_truncate("a" * 200, length=100)
        assert len(result) == 103  # 100 + '...'
        assert result.endswith("...")

    def test_custom_suffix(self):
        from app.services.exporter import _safe_truncate
        result = _safe_truncate("a" * 200, length=50, suffix="[…]")
        assert result.endswith("[…]")
        assert len(result) == 53

    def test_exact_length_not_truncated(self):
        from app.services.exporter import _safe_truncate
        result = _safe_truncate("a" * 100, length=100)
        assert result == "a" * 100

    def test_empty_string_returns_empty(self):
        from app.services.exporter import _safe_truncate
        assert _safe_truncate("") == ""

    def test_non_string_converted(self):
        from app.services.exporter import _safe_truncate
        assert _safe_truncate(42, length=100) == "42"


# ---------------------------------------------------------------------------
# _build_documents_inventory
# ---------------------------------------------------------------------------

class TestBuildDocumentsInventory:
    def test_empty_list(self):
        from app.services.exporter import _build_documents_inventory
        assert _build_documents_inventory([]) == []

    def test_single_document_small_size(self):
        from app.services.exporter import _build_documents_inventory
        doc = MagicMock()
        doc.file_size_kb = 512
        doc.original_name = "CCTP.pdf"
        doc.doc_type = "CCTP"
        doc.page_count = 25
        doc.ocr_quality_score = 0.95

        result = _build_documents_inventory([doc])
        assert len(result) == 1
        assert result[0]["name"] == "CCTP.pdf"
        assert result[0]["size_display"] == "512 Ko"
        assert result[0]["pages"] == 25

    def test_document_large_size_displayed_as_mo(self):
        from app.services.exporter import _build_documents_inventory
        doc = MagicMock()
        doc.file_size_kb = 2048
        doc.original_name = "Big.pdf"
        doc.doc_type = "DPGF"
        doc.page_count = 100
        doc.ocr_quality_score = 0.8

        result = _build_documents_inventory([doc])
        assert result[0]["size_display"] == "2.0 Mo"

    def test_document_none_fields(self):
        from app.services.exporter import _build_documents_inventory
        doc = MagicMock()
        doc.file_size_kb = None
        doc.original_name = "test.pdf"
        doc.doc_type = "RC"
        doc.page_count = None
        doc.ocr_quality_score = None

        result = _build_documents_inventory([doc])
        assert result[0]["size_display"] == "0 Ko"
        assert result[0]["pages"] == 0


# ---------------------------------------------------------------------------
# _fetch_company_logo_b64
# ---------------------------------------------------------------------------

class TestFetchCompanyLogoB64:
    @patch("app.services.exporter.logger")
    def test_returns_none_on_exception(self, mock_logger):
        from app.services.exporter import _fetch_company_logo_b64
        # Will fail trying to import/query DB
        result = _fetch_company_logo_b64("fake-org-id")
        assert result is None

    @patch("app.services.exporter.logger")
    def test_returns_none_when_org_id_invalid(self, mock_logger):
        from app.services.exporter import _fetch_company_logo_b64
        result = _fetch_company_logo_b64(None)
        assert result is None


# ---------------------------------------------------------------------------
# _generate_charts
# ---------------------------------------------------------------------------

class TestGenerateCharts:
    def test_returns_all_none_when_no_chart_module(self):
        from app.services.exporter import _generate_charts
        data = MagicMock()
        data.gonogo = None
        data.cashflow = None
        data.conflicts = None
        data.dpgf_pricing = None
        data.project.title = "Test AO"

        with patch("app.services.exporter.logger"):
            charts = _generate_charts(data)
        assert charts["radar_chart_b64"] is None
        assert charts["cashflow_chart_b64"] is None
        assert charts["heatmap_chart_b64"] is None
        assert charts["pricing_chart_b64"] is None

    def test_graceful_degradation_on_import_error(self):
        from app.services.exporter import _generate_charts
        data = MagicMock()
        data.project.title = "Test"
        data.gonogo = {"score": 7, "dimension_scores": {"tech": 8}}

        # Simulate chart_generator import failing
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "chart_generator" in name:
                raise ImportError("no matplotlib")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            charts = _generate_charts(data)
        # Should return None values, not raise
        assert isinstance(charts, dict)

    def test_charts_generated_when_gonogo_has_data(self):
        """Test chart generation with mocked chart_generator functions."""
        from app.services.exporter import _generate_charts

        data = MagicMock()
        data.project.title = "Projet X"
        data.gonogo = {"score": 8, "dimension_scores": {"tech": 9}}
        data.cashflow = None
        data.conflicts = None
        data.dpgf_pricing = None

        mock_fig = MagicMock()
        mock_radar = MagicMock(return_value=mock_fig)
        mock_to_b64 = MagicMock(return_value="base64radar")

        with patch.dict("sys.modules", {"app.services.chart_generator": MagicMock(
            generate_gonogo_radar=mock_radar,
            generate_cashflow_chart=MagicMock(),
            generate_risk_heatmap=MagicMock(),
            generate_pricing_benchmark_bars=MagicMock(),
            chart_to_base64=mock_to_b64,
        )}):
            charts = _generate_charts(data)
            assert charts["radar_chart_b64"] == "base64radar"
            assert charts["cashflow_chart_b64"] is None
