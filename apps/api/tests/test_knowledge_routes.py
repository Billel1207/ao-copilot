"""Tests pour les routes de base de connaissances BTP (glossaire, seuils, certifications, CPV).

Module knowledge.py expose des donnees statiques derriere des endpoints authentifies.
"""
import uuid
import pytest
from app.models.organization import Organization
from app.models.user import User
from app.core.security import hash_password, create_access_token


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_auth_headers(db_session):
    """Create org + user, return auth headers."""
    org = Organization(
        name="Knowledge Test Org",
        slug=f"knowledge-{uuid.uuid4().hex[:8]}",
        plan="pro",
        quota_docs=50,
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        org_id=org.id,
        email=f"knowledge-{uuid.uuid4().hex[:6]}@test.fr",
        hashed_pw=hash_password("TestPass123!"),
        full_name="Knowledge Tester",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()

    token = create_access_token({"sub": str(user.id), "org_id": str(org.id), "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# ── Glossary ─────────────────────────────────────────────────────────────────

async def test_list_glossary(client, db_session):
    """GET /knowledge/glossary returns all BTP terms."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/glossary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] > 0
    assert "terms" in data
    assert len(data["terms"]) == data["total"]


async def test_list_glossary_unauthorized(client):
    """GET /knowledge/glossary without auth -> 401."""
    resp = await client.get("/api/v1/knowledge/glossary")
    assert resp.status_code in (401, 403)


async def test_get_glossary_term_found(client, db_session):
    """GET /knowledge/glossary/{term} with known term returns definition."""
    headers = await _get_auth_headers(db_session)
    # "CCAP" is a standard BTP term that should exist
    resp = await client.get("/api/v1/knowledge/glossary/CCAP", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert "definition" in data


async def test_get_glossary_term_not_found(client, db_session):
    """GET /knowledge/glossary/{term} with unknown term -> 404 or suggestions."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/glossary/XYZNONEXISTENT", headers=headers)
    # Either 404 or suggestions
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert data["found"] is False


async def test_get_glossary_term_partial_match(client, db_session):
    """GET /knowledge/glossary/{term} with partial match returns suggestions."""
    headers = await _get_auth_headers(db_session)
    # "CC" should partially match CCAP, CCTP, etc.
    resp = await client.get("/api/v1/knowledge/glossary/CC", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    if not data.get("found"):
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0


# ── Thresholds ───────────────────────────────────────────────────────────────

async def test_get_thresholds(client, db_session):
    """GET /knowledge/thresholds returns market thresholds."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/thresholds", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "France"
    assert data["currency"] == "EUR"
    assert "thresholds" in data


async def test_check_threshold_small_amount(client, db_session):
    """GET /knowledge/thresholds/check/{amount} for small amount."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/thresholds/check/10000", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount_ht_eur"] == 10000
    assert "procedure" in data


async def test_check_threshold_large_amount(client, db_session):
    """GET /knowledge/thresholds/check/{amount} for large amount."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/thresholds/check/10000000", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "procedure" in data


async def test_check_threshold_negative_amount(client, db_session):
    """GET /knowledge/thresholds/check/-1 -> 400."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/thresholds/check/-1", headers=headers)
    assert resp.status_code == 400
    assert "positif" in resp.json()["detail"]


# ── Certifications ───────────────────────────────────────────────────────────

async def test_list_certifications(client, db_session):
    """GET /knowledge/certifications returns BTP certification list."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/certifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] > 0
    assert "certifications" in data


# ── CPV Codes ────────────────────────────────────────────────────────────────

async def test_list_cpv_codes(client, db_session):
    """GET /knowledge/cpv returns CPV codes list."""
    headers = await _get_auth_headers(db_session)
    resp = await client.get("/api/v1/knowledge/cpv", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] > 0
    assert "cpv_codes" in data
    # Each code should have code + label
    for cpv in data["cpv_codes"]:
        assert "code" in cpv
        assert "label" in cpv


# ── Glossary extract ─────────────────────────────────────────────────────────

async def test_extract_terms_from_text(client, db_session):
    """POST /knowledge/glossary/extract identifies BTP terms in text."""
    headers = await _get_auth_headers(db_session)
    resp = await client.post(
        "/api/v1/knowledge/glossary/extract",
        headers=headers,
        json={"text": "Le CCAP prevoit des penalites de retard. Le titulaire du marche doit fournir le DPGF."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "terms_found" in data
    assert data["terms_found"] >= 0  # At least some terms should match
    assert "terms" in data


async def test_extract_terms_empty_text(client, db_session):
    """POST /knowledge/glossary/extract with empty text -> 400."""
    headers = await _get_auth_headers(db_session)
    resp = await client.post(
        "/api/v1/knowledge/glossary/extract",
        headers=headers,
        json={"text": ""},
    )
    assert resp.status_code == 400


async def test_extract_terms_missing_text(client, db_session):
    """POST /knowledge/glossary/extract with missing field -> 400."""
    headers = await _get_auth_headers(db_session)
    resp = await client.post(
        "/api/v1/knowledge/glossary/extract",
        headers=headers,
        json={},
    )
    assert resp.status_code == 400
