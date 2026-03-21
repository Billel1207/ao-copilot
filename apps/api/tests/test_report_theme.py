"""Tests for app.core.report_theme — ReportTheme dataclass and get_theme()."""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import fields

from app.core.report_theme import (
    ReportTheme,
    DEFAULT_THEME,
    _ALLOWED_THEME_KEYS,
    get_theme,
    _theme_cache,
)


class TestReportThemeDefaults:
    """Test the ReportTheme dataclass default values."""

    def test_default_primary_color(self):
        theme = ReportTheme()
        assert theme.primary == "#2563EB"

    def test_default_header_bg(self):
        theme = ReportTheme()
        assert theme.header_bg == "#0F1B4C"
        assert theme.header_text == "#FFFFFF"

    def test_default_risk_colors_present(self):
        theme = ReportTheme()
        assert theme.risk_high_bg.startswith("#")
        assert theme.risk_med_bg.startswith("#")
        assert theme.risk_low_bg.startswith("#")

    def test_default_font_family(self):
        theme = ReportTheme()
        assert "Helvetica" in theme.font_family

    def test_default_font_sizes(self):
        theme = ReportTheme()
        assert theme.font_size_body == "11px"
        assert theme.font_size_h1 == "20px"

    def test_default_theme_is_report_theme(self):
        assert isinstance(DEFAULT_THEME, ReportTheme)

    def test_custom_override(self):
        theme = ReportTheme(primary="#FF0000", header_bg="#000000")
        assert theme.primary == "#FF0000"
        assert theme.header_bg == "#000000"
        # Other defaults remain
        assert theme.primary_dark == "#1D4ED8"


class TestAllowedThemeKeys:
    """Test the _ALLOWED_THEME_KEYS filtering logic."""

    def test_font_family_not_in_allowed(self):
        assert "font_family" not in _ALLOWED_THEME_KEYS

    def test_font_size_fields_not_in_allowed(self):
        for f in fields(ReportTheme):
            if f.name.startswith("font_size"):
                assert f.name not in _ALLOWED_THEME_KEYS

    def test_line_height_not_in_allowed(self):
        assert "line_height" not in _ALLOWED_THEME_KEYS

    def test_color_fields_in_allowed(self):
        assert "border_color" in _ALLOWED_THEME_KEYS

    def test_bg_fields_in_allowed(self):
        assert "header_bg" in _ALLOWED_THEME_KEYS
        assert "risk_high_bg" in _ALLOWED_THEME_KEYS
        assert "go_bg" in _ALLOWED_THEME_KEYS

    def test_text_fields_in_allowed(self):
        assert "header_text" in _ALLOWED_THEME_KEYS
        assert "risk_high_text" in _ALLOWED_THEME_KEYS

    def test_primary_in_allowed(self):
        assert "primary" in _ALLOWED_THEME_KEYS
        assert "primary_dark" in _ALLOWED_THEME_KEYS


class TestGetTheme:
    """Test get_theme() function with various inputs."""

    def setup_method(self):
        _theme_cache.clear()

    def test_no_org_id_returns_default(self):
        assert get_theme() is DEFAULT_THEME

    def test_none_org_id_returns_default(self):
        assert get_theme(None) is DEFAULT_THEME

    def test_empty_string_org_id_returns_default(self):
        assert get_theme("") is DEFAULT_THEME

    def test_cache_hit(self):
        org = "cached-org-id"
        custom = ReportTheme(primary="#FF0000")
        _theme_cache[org] = custom
        assert get_theme(org) is custom

    def test_exception_returns_default(self):
        """Any exception during DB query should return DEFAULT_THEME."""
        _theme_cache.clear()
        org = str(uuid.uuid4())
        # The import of SyncSessionLocal will fail -> exception -> default
        with patch.dict("sys.modules", {"app.core.database": None}):
            result = get_theme(org)
        assert result is DEFAULT_THEME

    def test_db_error_returns_default(self):
        """DB connection error should fallback gracefully."""
        org = str(uuid.uuid4())
        result = get_theme(org)
        assert result is DEFAULT_THEME
