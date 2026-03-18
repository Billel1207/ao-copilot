"""Tests pour le middleware API Key + scopes (deps.py).

Couvre :
- authenticate_api_key : lookup SHA-256, revoked, expired, last_used_at
- require_api_scope : scope valide, scope manquant, fallback JWT (None)
"""
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.api.v1.deps import authenticate_api_key, require_api_scope, SCOPE_COLUMN_MAP
from app.models.api_key import ApiKey


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_api_key(
    raw_key: str = "aoc_test_key_123456",
    is_active: bool = True,
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
    can_read_projects: bool = True,
    can_write_projects: bool = False,
    can_read_analysis: bool = True,
    can_trigger_analysis: bool = False,
    can_manage_billing: bool = False,
    can_export: bool = False,
) -> tuple[str, ApiKey]:
    """Return (raw_key, ApiKey ORM instance) with matching key_hash."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = MagicMock(spec=ApiKey)
    api_key.id = uuid.uuid4()
    api_key.key_hash = key_hash
    api_key.is_active = is_active
    api_key.revoked_at = revoked_at
    api_key.expires_at = expires_at
    api_key.last_used_at = None
    api_key.can_read_projects = can_read_projects
    api_key.can_write_projects = can_write_projects
    api_key.can_read_analysis = can_read_analysis
    api_key.can_trigger_analysis = can_trigger_analysis
    api_key.can_manage_billing = can_manage_billing
    api_key.can_export = can_export
    return raw_key, api_key


def _mock_db_with_key(api_key: ApiKey | None):
    """Return a mock AsyncSession that returns api_key on execute().scalar_one_or_none()."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = api_key
    db.execute.return_value = result_mock
    return db


# ── authenticate_api_key tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_api_key_header_returns_none():
    """Sans header X-API-Key, retourne None (fallback JWT)."""
    db = _mock_db_with_key(None)
    result = await authenticate_api_key(db=db, x_api_key=None)
    assert result is None
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_valid_api_key_returns_key():
    """Clé API valide avec bon hash → retourne l'objet ApiKey."""
    raw_key, api_key = _make_api_key()
    db = _mock_db_with_key(api_key)

    result = await authenticate_api_key(db=db, x_api_key=raw_key)
    assert result is api_key
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_valid_api_key_updates_last_used():
    """Clé API valide → last_used_at est mis à jour + flush appelé."""
    raw_key, api_key = _make_api_key()
    db = _mock_db_with_key(api_key)

    await authenticate_api_key(db=db, x_api_key=raw_key)
    assert api_key.last_used_at is not None
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_key_raises_401():
    """Clé inconnue (hash non trouvé en DB) → 401."""
    from fastapi import HTTPException

    db = _mock_db_with_key(None)  # Aucune clé trouvée
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_api_key(db=db, x_api_key="aoc_invalid_key")
    assert exc_info.value.status_code == 401
    assert "invalide" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_revoked_key_raises_403():
    """Clé révoquée (revoked_at set) → 403."""
    from fastapi import HTTPException

    raw_key, api_key = _make_api_key(
        revoked_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db = _mock_db_with_key(api_key)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_api_key(db=db, x_api_key=raw_key)
    assert exc_info.value.status_code == 403
    assert "révoquée" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_inactive_key_raises_403():
    """Clé désactivée (is_active=False) → 403."""
    from fastapi import HTTPException

    raw_key, api_key = _make_api_key(is_active=False)
    db = _mock_db_with_key(api_key)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_api_key(db=db, x_api_key=raw_key)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_expired_key_raises_403():
    """Clé expirée (expires_at dans le passé) → 403."""
    from fastapi import HTTPException

    raw_key, api_key = _make_api_key(
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db = _mock_db_with_key(api_key)

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_api_key(db=db, x_api_key=raw_key)
    assert exc_info.value.status_code == 403
    assert "expirée" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_key_not_expired_if_future():
    """Clé avec expires_at dans le futur → OK."""
    raw_key, api_key = _make_api_key(
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db = _mock_db_with_key(api_key)

    result = await authenticate_api_key(db=db, x_api_key=raw_key)
    assert result is api_key


@pytest.mark.asyncio
async def test_sha256_hash_lookup():
    """Le hash SHA-256 calculé correspond bien à celui en DB."""
    raw_key = "aoc_specific_test_key"
    expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    _, api_key = _make_api_key(raw_key=raw_key)
    assert api_key.key_hash == expected_hash


# ── require_api_scope tests ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scope_check_passes_with_correct_scope():
    """Clé API avec le scope requis → pas d'exception."""
    _, api_key = _make_api_key(can_read_projects=True)
    checker = require_api_scope("read:projects")
    # Should not raise
    await checker(api_key=api_key)


@pytest.mark.asyncio
async def test_scope_check_fails_without_scope():
    """Clé API sans le scope requis → 403."""
    from fastapi import HTTPException

    _, api_key = _make_api_key(can_write_projects=False)
    checker = require_api_scope("write:projects")

    with pytest.raises(HTTPException) as exc_info:
        await checker(api_key=api_key)
    assert exc_info.value.status_code == 403
    assert "write:projects" in exc_info.value.detail


@pytest.mark.asyncio
async def test_scope_check_multiple_scopes_all_required():
    """Plusieurs scopes requis, un manquant → 403."""
    from fastapi import HTTPException

    _, api_key = _make_api_key(can_read_projects=True, can_export=False)
    checker = require_api_scope("read:projects", "export")

    with pytest.raises(HTTPException) as exc_info:
        await checker(api_key=api_key)
    assert exc_info.value.status_code == 403
    assert "export" in exc_info.value.detail


@pytest.mark.asyncio
async def test_scope_check_bypassed_for_jwt():
    """Si api_key=None (auth JWT), le scope check est bypassé."""
    checker = require_api_scope("read:projects", "write:projects", "manage:billing")
    # Should not raise even with restrictive scopes — JWT user has full access
    await checker(api_key=None)


@pytest.mark.asyncio
async def test_scope_unknown_scope_raises_500():
    """Scope inconnu dans SCOPE_COLUMN_MAP → 500."""
    from fastapi import HTTPException

    _, api_key = _make_api_key()
    checker = require_api_scope("unknown:scope")

    with pytest.raises(HTTPException) as exc_info:
        await checker(api_key=api_key)
    assert exc_info.value.status_code == 500
    assert "inconnu" in exc_info.value.detail.lower()


def test_scope_column_map_covers_all_scopes():
    """Vérifie que SCOPE_COLUMN_MAP contient les scopes documentés."""
    expected_scopes = {
        "read:projects", "write:projects", "read:analysis",
        "trigger:analysis", "manage:billing", "export",
    }
    assert set(SCOPE_COLUMN_MAP.keys()) == expected_scopes
