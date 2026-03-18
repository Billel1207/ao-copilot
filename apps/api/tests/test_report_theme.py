"""Tests pour app/core/report_theme.py — ReportTheme, DEFAULT_THEME, get_theme."""
import re

from app.core.report_theme import ReportTheme, DEFAULT_THEME, get_theme


class TestReportTheme:
    def test_default_theme_is_report_theme(self):
        assert isinstance(DEFAULT_THEME, ReportTheme)

    def test_get_theme_returns_default(self):
        assert get_theme() is DEFAULT_THEME

    def test_all_color_fields_are_valid_hex(self):
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        color_fields = [
            "primary", "primary_dark", "header_bg", "header_text",
            "risk_high_bg", "risk_high_text", "risk_med_bg", "risk_med_text",
            "risk_low_bg", "risk_low_text", "info_bg", "info_text",
            "neutral_bg", "border_color", "text_primary", "text_secondary", "text_muted",
            "go_bg", "go_text", "nogo_bg", "nogo_text",
            "conditional_bg", "conditional_text",
        ]
        for field_name in color_fields:
            value = getattr(DEFAULT_THEME, field_name)
            assert hex_pattern.match(value), f"{field_name} = {value!r} is not valid hex"

    def test_font_sizes_contain_px(self):
        size_fields = [
            "font_size_body", "font_size_small",
            "font_size_h1", "font_size_h2", "font_size_h3",
        ]
        for field_name in size_fields:
            value = getattr(DEFAULT_THEME, field_name)
            assert "px" in value, f"{field_name} = {value!r} does not contain 'px'"
