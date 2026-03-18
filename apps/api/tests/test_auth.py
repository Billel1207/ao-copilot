"""Tests pour l'authentification (register / login / refresh / logout)."""
import pytest
REGISTER_PAYLOAD = {
    "email": "test@aocopilot.fr",
    "password": "SecurePass123!",
    "full_name": "Jean Dupont",
    "org_name": "BTP Dupont SAS",
}

async def test_register_creates_org_and_user(client):
    """L'inscription crée une organisation et un utilisateur admin."""
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["full_name"] == REGISTER_PAYLOAD["full_name"]
    assert "id" in data
    assert "org_id" in data

async def test_register_duplicate_email_returns_400(client):
    """Deux inscriptions avec le même email → 400."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 400

async def test_login_returns_access_token(client):
    """Le login renvoie un access_token valide."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0

async def test_login_wrong_password_returns_401(client):
    """Mauvais mot de passe → 401."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "WRONG_PASSWORD"},
    )
    assert resp.status_code == 401

async def test_me_requires_auth(client):
    """GET /me sans token → 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

async def test_me_returns_user_with_token(client):
    """GET /me avec token valide → infos utilisateur."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
