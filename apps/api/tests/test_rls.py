"""Tests isolation multi-tenant — chaque org ne voit que ses propres données."""
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.project import AoProject
from app.models.document import AoDocument
from app.core.security import create_access_token
# ── Helpers ────────────────────────────────────────────────────────────────
def _make_headers(user_id: str, org_id: str, role: str = "admin") -> dict:
    token = create_access_token({"sub": user_id, "org_id": org_id, "role": role})
    return {"Authorization": f"Bearer {token}"}
async def _create_tenant(
    db: AsyncSession, suffix: str, plan: str = "pro", quota: int = 60
) -> tuple[Organization, User]:
    org = Organization(
        id=uuid.uuid4(),
        name=f"Tenant {suffix}",
        slug=f"tenant-{suffix}-{uuid.uuid4().hex[:6]}",
        plan=plan,
        quota_docs=quota,
    )
    db.add(org)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=f"user-{suffix}-{uuid.uuid4().hex[:6]}@test.com",
        hashed_pw="hashed",
        role="admin",
        full_name=f"User {suffix}",
    )
    db.add(user)
    await db.flush()
    return org, user
async def _create_project(
    db: AsyncSession, org: Organization, user: User, title: str
) -> AoProject:
    project = AoProject(
        id=uuid.uuid4(),
        org_id=org.id,
        created_by=user.id,
        title=title,
        status="draft",
    )
    db.add(project)
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
# ── Tests — Isolation des projets ─────────────────────────────────────────
class TestProjectIsolation:
    """Les projets d'une org ne sont pas visibles par une autre org."""


    async def test_tenant_a_cannot_see_tenant_b_projects(self, client_db):
        client, db = client_db

        # Créer deux tenants
        org_a, user_a = await _create_tenant(db, "alpha")
        org_b, user_b = await _create_tenant(db, "beta")

        # Créer un projet pour chaque org
        proj_a = await _create_project(db, org_a, user_a, "Projet Alpha — Lycée")
        proj_b = await _create_project(db, org_b, user_b, "Projet Beta — Hôpital")

        # Tenant A ne voit que son projet
        headers_a = _make_headers(str(user_a.id), str(org_a.id))
        resp_a = await client.get("/api/v1/projects", headers=headers_a)
        assert resp_a.status_code == 200, resp_a.text
        # list_projects returns ProjectListOut with items and total
        projects_a = resp_a.json()

        titles_a = [p["title"] for p in projects_a["items"]]
        assert "Projet Alpha — Lycée" in titles_a
        assert "Projet Beta — Hôpital" not in titles_a

        # Tenant B ne voit que son projet
        headers_b = _make_headers(str(user_b.id), str(org_b.id))
        resp_b = await client.get("/api/v1/projects", headers=headers_b)
        assert resp_b.status_code == 200
        projects_b = resp_b.json()

        titles_b = [p["title"] for p in projects_b["items"]]
        assert "Projet Beta — Hôpital" in titles_b
        assert "Projet Alpha — Lycée" not in titles_b


    async def test_tenant_cannot_access_other_project_by_id(self, client_db):
        client, db = client_db

        org_a, user_a = await _create_tenant(db, "gamma")
        org_b, user_b = await _create_tenant(db, "delta")

        proj_b = await _create_project(db, org_b, user_b, "Projet Secret Delta")

        # Tenant A tente d'accéder au projet de B par son ID
        headers_a = _make_headers(str(user_a.id), str(org_a.id))
        resp = await client.get(
            f"/api/v1/projects/{proj_b.id}", headers=headers_a
        )
        # Doit être 404 ou 403
        assert resp.status_code in (403, 404)
# ── Tests — Isolation des documents ───────────────────────────────────────
class TestDocumentIsolation:
    """Les documents d'un tenant ne sont pas accessibles par un autre."""


    async def test_tenant_sees_only_own_docs(self, client_db):
        client, db = client_db

        org_a, user_a = await _create_tenant(db, "epsilon")
        org_b, user_b = await _create_tenant(db, "zeta")

        proj_a = await _create_project(db, org_a, user_a, "Projet Epsilon")
        proj_b = await _create_project(db, org_b, user_b, "Projet Zeta")

        # Docs pour A
        for i in range(2):
            db.add(AoDocument(
                id=uuid.uuid4(),
                project_id=proj_a.id,
                original_name=f"epsilon_{i}.pdf",
                s3_key=f"epsilon/{i}.pdf",
                doc_type="RC",
                status="done",
            ))

        # Docs pour B
        for i in range(3):
            db.add(AoDocument(
                id=uuid.uuid4(),
                project_id=proj_b.id,
                original_name=f"zeta_{i}.pdf",
                s3_key=f"zeta/{i}.pdf",
                doc_type="CCTP",
                status="done",
            ))
        await db.flush()

        # A ne voit que ses 2 docs
        headers_a = _make_headers(str(user_a.id), str(org_a.id))
        resp_a = await client.get(
            f"/api/v1/projects/{proj_a.id}/documents", headers=headers_a
        )
        assert resp_a.status_code == 200
        docs_a = resp_a.json()
        assert len(docs_a) == 2
        assert all("epsilon" in d["original_name"] for d in docs_a)
# ── Tests — Isolation du billing ──────────────────────────────────────────
class TestBillingIsolation:
    """Les stats de consommation sont isolées par org."""


    async def test_usage_reflects_only_own_org_docs(self, client_db):
        client, db = client_db

        org_a, user_a = await _create_tenant(db, "eta", quota=50)
        org_b, user_b = await _create_tenant(db, "theta", quota=50)

        proj_a = await _create_project(db, org_a, user_a, "Billing A")
        proj_b = await _create_project(db, org_b, user_b, "Billing B")

        # 5 docs pour A, 10 docs pour B
        for i in range(5):
            db.add(AoDocument(
                id=uuid.uuid4(),
                project_id=proj_a.id,
                original_name=f"a_{i}.pdf",
                s3_key=f"a/{i}.pdf",
                doc_type="AUTRES",
                status="done",
            ))
        for i in range(10):
            db.add(AoDocument(
                id=uuid.uuid4(),
                project_id=proj_b.id,
                original_name=f"b_{i}.pdf",
                s3_key=f"b/{i}.pdf",
                doc_type="AUTRES",
                status="done",
            ))
        await db.flush()

        # A voit 5 docs utilisés, pas 15
        headers_a = _make_headers(str(user_a.id), str(org_a.id))
        resp_a = await client.get("/api/v1/billing/usage", headers=headers_a)
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["docs_used_this_month"] == 5

        # B voit 10 docs utilisés, pas 15
        headers_b = _make_headers(str(user_b.id), str(org_b.id))
        resp_b = await client.get("/api/v1/billing/usage", headers=headers_b)
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["docs_used_this_month"] == 10
# ── Tests — Isolation de la suppression GDPR ──────────────────────────────
class TestGdprIsolation:
    """La suppression d'un tenant ne touche pas un autre."""


    async def test_delete_one_org_does_not_affect_other(self, client_db):
        client, db = client_db

        org_a, user_a = await _create_tenant(db, "iota")
        org_b, user_b = await _create_tenant(db, "kappa")
        user_a.role = "owner"
        user_b.role = "owner"
        await db.flush()

        # Supprimer org A
        headers_a = _make_headers(str(user_a.id), str(org_a.id), role="owner")
        resp = await client.post("/api/v1/account/delete", headers=headers_a)
        assert resp.status_code == 202

        # Org B est toujours intacte
        await db.refresh(org_b)
        assert org_b.deleted_at is None

        await db.refresh(user_b)
        assert "anonymized" not in user_b.email and "deleted" not in user_b.email
        assert user_b.full_name == "User kappa"
