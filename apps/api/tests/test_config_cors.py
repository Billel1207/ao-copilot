"""Tests pour la validation CORS stricte dans config.py.

Couvre :
- Production : wildcard "*" → RuntimeError
- Production : origin HTTP → RuntimeError
- Dev : HTTP localhost → OK
- Dev : parsing de multiples origins
"""
import pytest
from unittest.mock import patch

from app.config import Settings


def _make_settings(**overrides) -> Settings:
    """Crée un objet Settings avec des valeurs de test sans toucher à l'env."""
    defaults = {
        "APP_ENV": "development",
        "SECRET_KEY": "test-secret-key-minimum-32-characters-long",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "DATABASE_URL_SYNC": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "ANTHROPIC_API_KEY": "test-key",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_production_wildcard_raises():
    """En production, ALLOWED_ORIGINS='*' lève RuntimeError."""
    s = _make_settings(APP_ENV="production", ALLOWED_ORIGINS="*")
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS contains '\\*'"):
        _ = s.allowed_origins_list


def test_production_http_origin_raises():
    """En production, un origin HTTP (non-HTTPS) lève RuntimeError."""
    s = _make_settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="http://example.com",
    )
    with pytest.raises(RuntimeError, match="non-HTTPS origin"):
        _ = s.allowed_origins_list


def test_production_https_origin_ok():
    """En production, un origin HTTPS est accepté."""
    s = _make_settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="https://ao-copilot.fr",
    )
    result = s.allowed_origins_list
    assert result == ["https://ao-copilot.fr"]


def test_production_multiple_https_ok():
    """En production, plusieurs origins HTTPS séparés par des virgules."""
    s = _make_settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="https://ao-copilot.fr, https://app.ao-copilot.fr",
    )
    result = s.allowed_origins_list
    assert len(result) == 2
    assert "https://ao-copilot.fr" in result
    assert "https://app.ao-copilot.fr" in result


def test_production_mixed_http_https_raises():
    """En production, un mix HTTP + HTTPS lève RuntimeError sur le HTTP."""
    s = _make_settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="https://ao-copilot.fr,http://admin.ao-copilot.fr",
    )
    with pytest.raises(RuntimeError, match="non-HTTPS"):
        _ = s.allowed_origins_list


def test_dev_http_localhost_ok():
    """En développement, HTTP localhost est autorisé."""
    s = _make_settings(
        APP_ENV="development",
        ALLOWED_ORIGINS="http://localhost:3000",
    )
    result = s.allowed_origins_list
    assert result == ["http://localhost:3000"]


def test_dev_wildcard_ok():
    """En développement, wildcard '*' est autorisé (pas de guard en dev)."""
    s = _make_settings(APP_ENV="development", ALLOWED_ORIGINS="*")
    result = s.allowed_origins_list
    assert result == ["*"]


def test_empty_origins_returns_empty_list():
    """ALLOWED_ORIGINS vide → liste vide."""
    s = _make_settings(ALLOWED_ORIGINS="")
    result = s.allowed_origins_list
    assert result == []


def test_whitespace_trimmed():
    """Les espaces autour des origins sont nettoyés."""
    s = _make_settings(
        ALLOWED_ORIGINS="  http://localhost:3000 , http://localhost:8080  ",
    )
    result = s.allowed_origins_list
    assert result == ["http://localhost:3000", "http://localhost:8080"]
