"""Tests for company profile routes — GET/PUT /company/profile + logo upload/delete.

Pure unit tests using the async test client with mocked DB session.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.models.organization import Organization
from app.models.user import User
from app.core.security import hash_password, create_access_token


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_auth_context(db_session, plan="pro"):
    """Create org + user in DB, return (org, user, headers)."""
    org = Organization(
        name="Company Test Org",
        slug=f"company-test-{uuid.uuid4().hex[:8]}",
        plan=plan,
        quota_docs=50,
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        org_id=org.id,
        email=f"company-{uuid.uuid4().hex[:6]}@test.fr",
        hashed_pw=hash_password("TestPass123!"),
        full_name="Company Tester",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()

    token_data = {"sub": str(user.id), "org_id": str(org.id), "role": user.role}
    token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {token}"}

    return org, user, headers


# ── GET /company/profile ─────────────────────────────────────────────────────

async def test_get_profile_not_found(client, db_session):
    """GET profile when none exists -> 404."""
    _, _, headers = await _create_auth_context(db_session)
    resp = await client.get("/api/v1/company/profile", headers=headers)
    assert resp.status_code == 404
    assert "profil" in resp.json()["detail"].lower()


async def test_get_profile_success(client, db_session):
    """GET profile when one exists -> 200 with profile data."""
    org, _, headers = await _create_auth_context(db_session)

    from app.models.company_profile import CompanyProfile
    profile = CompanyProfile(
        org_id=org.id,
        revenue_eur=5_000_000,
        employee_count=25,
        certifications=["ISO 9001"],
        specialties=["gros oeuvre"],
        regions=["Ile-de-France"],
        max_market_size_eur=2_000_000,
    )
    db_session.add(profile)
    await db_session.flush()

    resp = await client.get("/api/v1/company/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_eur"] == 5_000_000
    assert data["employee_count"] == 25
    assert "ISO 9001" in data["certifications"]
    assert data["org_id"] == str(org.id)


async def test_get_profile_unauthorized(client, db_session):
    """GET profile without auth -> 401/403."""
    resp = await client.get("/api/v1/company/profile")
    assert resp.status_code in (401, 403)


# ── PUT /company/profile ─────────────────────────────────────────────────────

async def test_create_profile_via_put(client, db_session):
    """PUT profile when none exists -> creates new profile."""
    _, _, headers = await _create_auth_context(db_session)

    body = {
        "revenue_eur": 3_000_000,
        "employee_count": 15,
        "certifications": ["Qualibat 2111", "RGE"],
        "specialties": ["plomberie"],
        "regions": ["PACA"],
        "max_market_size_eur": 1_000_000,
    }
    resp = await client.put("/api/v1/company/profile", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_eur"] == 3_000_000
    assert data["employee_count"] == 15
    assert "Qualibat 2111" in data["certifications"]


async def test_update_profile_via_put(client, db_session):
    """PUT profile when one already exists -> updates it."""
    org, _, headers = await _create_auth_context(db_session)

    from app.models.company_profile import CompanyProfile
    profile = CompanyProfile(
        org_id=org.id,
        revenue_eur=1_000_000,
        employee_count=5,
        certifications=[],
        specialties=[],
        regions=[],
    )
    db_session.add(profile)
    await db_session.flush()

    body = {
        "revenue_eur": 8_000_000,
        "employee_count": 40,
        "certifications": ["ISO 14001"],
        "specialties": ["electricite"],
        "regions": ["Bretagne"],
        "max_market_size_eur": 5_000_000,
        "assurance_rc_montant": 3_000_000,
        "assurance_decennale": True,
        "marge_minimale_pct": 10.0,
        "max_projets_simultanes": 8,
        "projets_actifs_count": 3,
    }
    resp = await client.put("/api/v1/company/profile", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_eur"] == 8_000_000
    assert data["assurance_decennale"] is True
    assert data["marge_minimale_pct"] == 10.0


async def test_put_profile_with_minimal_data(client, db_session):
    """PUT profile with only optional fields -> creates profile with nulls."""
    _, _, headers = await _create_auth_context(db_session)

    body = {}  # All fields are optional
    resp = await client.put("/api/v1/company/profile", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_eur"] is None
    assert data["certifications"] == []


async def test_put_profile_unauthorized(client, db_session):
    """PUT profile without auth -> 401/403."""
    resp = await client.put("/api/v1/company/profile", json={"revenue_eur": 100})
    assert resp.status_code in (401, 403)


# ── POST /company/logo ───────────────────────────────────────────────────────

async def test_upload_logo_invalid_type(client, db_session):
    """Upload non-image file -> 400."""
    _, _, headers = await _create_auth_context(db_session)

    resp = await client.post(
        "/api/v1/company/logo",
        headers=headers,
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 400
    assert "type" in resp.json()["detail"].lower()


async def test_upload_logo_too_large(client, db_session):
    """Upload file > 2MB -> 400."""
    _, _, headers = await _create_auth_context(db_session)

    large_content = b"x" * (3 * 1024 * 1024)  # 3 MB
    resp = await client.post(
        "/api/v1/company/logo",
        headers=headers,
        files={"file": ("logo.png", large_content, "image/png")},
    )
    assert resp.status_code == 400
    assert "volumineux" in resp.json()["detail"].lower()


async def test_upload_logo_success_no_existing_profile(client, db_session):
    """Upload logo when no profile exists -> creates profile with logo."""
    _, _, headers = await _create_auth_context(db_session)

    small_png = b"\x89PNG\r\n\x1a\n" + b"x" * 100  # fake PNG

    with patch("app.services.storage.storage_service") as mock_storage:
        mock_storage.upload_bytes = MagicMock()
        resp = await client.post(
            "/api/v1/company/logo",
            headers=headers,
            files={"file": ("logo.png", small_png, "image/png")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "logo_s3_key" in data


async def test_upload_logo_success_replaces_existing(client, db_session):
    """Upload logo when profile with logo exists -> replaces old logo."""
    org, _, headers = await _create_auth_context(db_session)

    from app.models.company_profile import CompanyProfile
    profile = CompanyProfile(
        org_id=org.id,
        logo_s3_key="logos/old_logo.png",
    )
    db_session.add(profile)
    await db_session.flush()

    small_png = b"\x89PNG\r\n\x1a\n" + b"x" * 100

    with patch("app.services.storage.storage_service") as mock_storage:
        mock_storage.upload_bytes = MagicMock()
        mock_storage.delete_object = MagicMock()
        resp = await client.post(
            "/api/v1/company/logo",
            headers=headers,
            files={"file": ("new_logo.jpg", small_png, "image/jpeg")},
        )

    assert resp.status_code == 200
    # Old logo should have been deleted
    mock_storage.delete_object.assert_called_once_with("logos/old_logo.png")


# ── DELETE /company/logo ─────────────────────────────────────────────────────

async def test_delete_logo_no_profile(client, db_session):
    """DELETE logo when no profile exists -> 404."""
    _, _, headers = await _create_auth_context(db_session)

    resp = await client.delete("/api/v1/company/logo", headers=headers)
    assert resp.status_code == 404


async def test_delete_logo_no_logo_set(client, db_session):
    """DELETE logo when profile exists but no logo -> 404."""
    org, _, headers = await _create_auth_context(db_session)

    from app.models.company_profile import CompanyProfile
    profile = CompanyProfile(org_id=org.id)
    db_session.add(profile)
    await db_session.flush()

    resp = await client.delete("/api/v1/company/logo", headers=headers)
    assert resp.status_code == 404
    assert "logo" in resp.json()["detail"].lower()


async def test_delete_logo_success(client, db_session):
    """DELETE logo when logo exists -> 200 and clears s3 key."""
    org, _, headers = await _create_auth_context(db_session)

    from app.models.company_profile import CompanyProfile
    profile = CompanyProfile(
        org_id=org.id,
        logo_s3_key="logos/to_delete.png",
    )
    db_session.add(profile)
    await db_session.flush()

    with patch("app.services.storage.storage_service") as mock_storage:
        mock_storage.delete_object = MagicMock()
        resp = await client.delete("/api/v1/company/logo", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    mock_storage.delete_object.assert_called_once_with("logos/to_delete.png")
