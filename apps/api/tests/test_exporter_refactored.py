"""Tests pour app/services/exporter.py — template loading et re-exports."""
import os


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
