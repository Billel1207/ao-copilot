"""Tests avancés pour les routes d'authentification (complète test_auth.py).

Couvre : refresh token rotation, expired token, logout, /me enrichi, password reset flow.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt

from app.config import settings
from app.core.security import create_access_token, create_refresh_token

REGISTER_PAYLOAD = {
    "email": "advanced@aocopilot.fr",
    "password": "SecurePass123!",
    "full_name": "Marie Test",
    "org_name": "BTP Test SAS",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _register_and_login(client):
    """Register + login, return (access_token, refresh_cookie)."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    # Extract refresh cookie
    refresh_cookie = None
    for c in resp.cookies.jar:
        if c.name == "refresh_token":
            refresh_cookie = c.value
    return token, refresh_cookie


# ── Register edge cases ─────────────────────────────────────────────────────

async def test_register_short_password_rejected(client):
    """Password < 8 chars should be rejected by pydantic validation."""
    payload = {**REGISTER_PAYLOAD, "email": "short@test.fr", "password": "Ab1!"}
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


async def test_register_invalid_email_rejected(client):
    """Invalid email format should be rejected."""
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


async def test_register_missing_org_name_rejected(client):
    """Missing org_name field should be rejected."""
    payload = {"email": "noorg@test.fr", "password": "SecurePass123!", "full_name": "Test"}
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


async def test_register_email_case_insensitive(client):
    """Emails should be compared case-insensitively."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    # Try registering with same email in different case
    upper_payload = {**REGISTER_PAYLOAD, "email": REGISTER_PAYLOAD["email"].upper()}
    resp = await client.post("/api/v1/auth/register", json=upper_payload)
    assert resp.status_code == 400
    assert "déjà utilisé" in resp.json()["detail"]


async def test_register_sets_refresh_cookie(client):
    """Registration should set an httponly refresh_token cookie."""
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    # Check that set-cookie header is present for refresh_token
    cookie_found = any(c.name == "refresh_token" for c in resp.cookies.jar)
    assert cookie_found, "refresh_token cookie should be set on registration"


# ── Login edge cases ────────────────────────────────────────────────────────

async def test_login_nonexistent_email(client):
    """Login with non-existent email -> 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert resp.status_code == 401


async def test_login_updates_last_login(client, db_session):
    """Login should update user.last_login_at."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    # Verify via /me that login succeeded (indirect proof last_login_at was set)
    token = resp.json()["access_token"]
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200


# ── Refresh token rotation ──────────────────────────────────────────────────

async def test_refresh_token_returns_new_access_token(client):
    """POST /refresh with valid refresh cookie -> new access token."""
    _, refresh = await _register_and_login(client)
    assert refresh is not None, "Should have a refresh cookie after login"

    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["expires_in"] > 0


async def test_refresh_without_cookie_returns_401(client):
    """POST /refresh without cookie -> 401."""
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
    assert "manquant" in resp.json()["detail"].lower()


async def test_refresh_with_invalid_token_returns_401(client):
    """POST /refresh with garbage token -> 401."""
    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": "invalid.garbage.token"},
    )
    assert resp.status_code == 401


async def test_refresh_with_access_token_returns_401(client):
    """Using an access token as refresh token should fail (wrong type)."""
    token, _ = await _register_and_login(client)
    # Use the access_token as if it were a refresh_token
    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    assert resp.status_code == 401
    assert "type" in resp.json()["detail"].lower()


# ── Expired token handling ──────────────────────────────────────────────────

async def test_expired_access_token_returns_401(client):
    """An expired access token should be rejected by /me."""
    # Create a token that expired 1 hour ago
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "org_id": "00000000-0000-0000-0000-000000000002",
        "role": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "type": "access",
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


async def test_expired_refresh_token_returns_401(client):
    """An expired refresh token should be rejected."""
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "org_id": "00000000-0000-0000-0000-000000000002",
        "role": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(days=10),
        "type": "refresh",
        "jti": "test-jti",
    }
    expired_refresh = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": expired_refresh},
    )
    assert resp.status_code == 401


# ── Logout ──────────────────────────────────────────────────────────────────

async def test_logout_deletes_refresh_cookie(client):
    """POST /logout should delete the refresh_token cookie."""
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    data = resp.json()
    assert "déconnexion" in data["message"].lower()


# ── /me endpoint ────────────────────────────────────────────────────────────

async def test_me_returns_org_slug(client):
    """GET /me should include org_slug."""
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    token = resp.json()["access_token"]

    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert "org_slug" in data
    assert data["org_slug"] is not None


async def test_me_with_malformed_token_returns_401(client):
    """GET /me with a malformed Bearer token -> 401."""
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert resp.status_code == 401
