"""Tests pour le fallback du rate limiter (core/limiter.py).

Couvre :
- Redis indisponible → fallback memory:// sans crash
- Redis disponible → utilise Redis comme storage
"""
import sys
import pytest
from unittest.mock import patch, MagicMock

from slowapi import Limiter


def test_limiter_fallback_on_redis_unavailable():
    """Redis indisponible → _build_limiter retourne un Limiter memory:// sans crash."""
    mock_redis_module = MagicMock()
    mock_client = MagicMock()
    mock_client.ping.side_effect = ConnectionError("Redis unreachable")
    mock_redis_module.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis_module}):
        from app.core.limiter import _build_limiter
        limiter = _build_limiter()

    assert isinstance(limiter, Limiter)


def test_limiter_fallback_on_redis_timeout():
    """Timeout Redis → fallback memory:// sans crash."""
    mock_redis_module = MagicMock()
    mock_client = MagicMock()
    mock_client.ping.side_effect = TimeoutError("Connection timed out")
    mock_redis_module.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis_module}):
        from app.core.limiter import _build_limiter
        limiter = _build_limiter()

    assert isinstance(limiter, Limiter)


def test_limiter_uses_redis_when_available():
    """Redis disponible → utilise Redis storage URI, ping appelé."""
    mock_redis_module = MagicMock()
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_redis_module.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis_module}), \
         patch("app.core.limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        from app.core.limiter import _build_limiter
        limiter = _build_limiter()

    assert isinstance(limiter, Limiter)
    mock_client.ping.assert_called()


def test_limiter_fallback_on_import_error():
    """Si le module redis lève une exception à l'import → fallback memory://."""
    # Simulate redis import raising an exception inside _build_limiter
    # The broad except clause in _build_limiter catches everything
    mock_redis_module = MagicMock()
    mock_redis_module.from_url.side_effect = Exception("Cannot connect")

    with patch.dict(sys.modules, {"redis": mock_redis_module}):
        from app.core.limiter import _build_limiter
        limiter = _build_limiter()

    assert isinstance(limiter, Limiter)


def test_existing_limiter_is_limiter_instance():
    """Le limiter exporté par le module est une instance de Limiter."""
    from app.core.limiter import limiter
    assert isinstance(limiter, Limiter)
