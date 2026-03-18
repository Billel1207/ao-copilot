"""Tests GDPR — droit à l'effacement, export données, préférences email."""
import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.company_profile import CompanyProfile
from app.core.security import create_access_token


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_headers(user_id: str, role: str = "owner") -> dict:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _create_org_user(
    db: AsyncSession, role: str = "owner", plan: str = "pro"
) -> tuple[Organization, User]:
    org = Organization(
        id=uuid.uuid4(),
        name=f"GDPR Test Org {uuid.uuid4().hex[:6]}",
        slug=f"gdpr-org-{uuid.uuid4().hex[:6]}",
        plan=plan,
        quota_docs=60,
    )
    db.add(org)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=f"gdpr-{uuid.uuid4().hex[:6]}@test.com",
        hashed_pw="hashed",
        role=role,
        full_name="GDPR Test User",
    )
    db.add(user)
    await db.flush()
    return org, user


async def _seed_project_with_docs(
    db: AsyncSession, org: Organization, user: User, n_docs: int = 2
) -> AoProject:
    project = AoProject(
        id=uuid.uuid4(),
        org_id=org.id,
        created_by=user.id,
        title="Projet GDPR test",
        status="ready",
    )
    db.add(project)
    await db.flush()

    for i in range(n_docs):
        doc = AoDocument(
            id=uuid.uuid4(),
            project_id=project.id,
            original_name=f"gdpr_doc_{i}.pdf",
            s3_key=f"test/gdpr_doc_{i}.pdf",
            doc_type="RC",
            status="done",
        )
        db.add(doc)
    await db.flush()
    return project


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client_db(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, db_session
    app.dependency_overrides.clear()


# ── Tests — Suppression de compte ─────────────────────────────────────────


class TestAccountDeletion:
    """POST /api/v1/account/delete — soft-delete org + anonymise users."""

    @pytest.mark.asyncio
    async def test_owner_can_request_deletion(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, role="owner")
        headers = _make_headers(str(user.id), role="owner")

        resp = await client.post("/api/v1/account/delete", headers=headers)
        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert "deleted_at" in data
        assert data["org_id"] == str(org.id)

        # Vérifier que l'org est soft-deleted
        await db.refresh(org)
        assert org.deleted_at is not None

        # Vérifier que l'utilisateur est anonymisé
        await db.refresh(user)
        assert "anonymized" in user.email
        assert user.full_name == "Compte supprimé"
        assert user.hashed_pw == "DELETED"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, role="member")
        headers = _make_headers(str(user.id), role="member")

        resp = await client.post("/api/v1/account/delete", headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_deletion_anonymises_all_org_users(self, client_db):
        client, db = client_db
        org, owner = await _create_org_user(db, role="owner")

        # Ajouter un deuxième utilisateur
        member = User(
            id=uuid.uuid4(),
            org_id=org.id,
            email=f"member-{uuid.uuid4().hex[:6]}@test.com",
            hashed_pw="hashed",
            role="member",
            full_name="Marie Martin",
        )
        db.add(member)
        await db.flush()

        headers = _make_headers(str(owner.id), role="owner")
        resp = await client.post("/api/v1/account/delete", headers=headers)
        assert resp.status_code == 202

        await db.refresh(member)
        assert "anonymized" in member.email
        assert member.full_name == "Compte supprimé"


# ── Tests — Export de données ─────────────────────────────────────────────


class TestDataExport:
    """GET /api/v1/account/export — export JSON RGPD Art. 20."""

    @pytest.mark.asyncio
    async def test_export_returns_user_data(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db)
        headers = _make_headers(str(user.id))

        resp = await client.get("/api/v1/account/export", headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "export_date" in data
        assert data["user"]["email"] == user.email
        assert data["user"]["full_name"] == user.full_name
        assert data["organization"]["name"] == org.name
        assert data["organization"]["plan"] == org.plan

    @pytest.mark.asyncio
    async def test_export_includes_projects_and_docs(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db)
        project = await _seed_project_with_docs(db, org, user, n_docs=3)
        headers = _make_headers(str(user.id))

        resp = await client.get("/api/v1/account/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == "Projet GDPR test"
        assert len(data["documents"]) == 3

    @pytest.mark.asyncio
    async def test_export_includes_company_profile(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db)
        profile = CompanyProfile(
            id=uuid.uuid4(),
            org_id=org.id,
            company_name="BTP Test SAS",
            siret="12345678901234",
            revenue_annual_eur=2_000_000,
            employee_count=25,
        )
        db.add(profile)
        await db.flush()
        headers = _make_headers(str(user.id))

        resp = await client.get("/api/v1/account/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["company_profile"] is not None
        assert data["company_profile"]["company_name"] == "BTP Test SAS"
        assert data["company_profile"]["siret"] == "12345678901234"

    @pytest.mark.asyncio
    async def test_export_unauthenticated_returns_401(self, client_db):
        client, _ = client_db
        resp = await client.get("/api/v1/account/export")
        assert resp.status_code in (401, 403)


# ── Tests — Désabonnement emails ──────────────────────────────────────────


class TestEmailUnsubscribe:
    """POST /api/v1/account/unsubscribe-emails — préférence email RGPD."""

    @pytest.mark.asyncio
    async def test_unsubscribe_succeeds(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db)
        headers = _make_headers(str(user.id))

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            resp = await client.post(
                "/api/v1/account/unsubscribe-emails", headers=headers
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "désabonné" in data["message"]
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_redis_failure_returns_500(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db)
        headers = _make_headers(str(user.id))

        with patch("redis.from_url", side_effect=Exception("Redis down")):
            resp = await client.post(
                "/api/v1/account/unsubscribe-emails", headers=headers
            )

        assert resp.status_code == 500
