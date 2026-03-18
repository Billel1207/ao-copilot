"""Tests upload de documents — magic bytes, quota, multi-tenant isolation."""
import pytest
import pytest_asyncio
import uuid
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.project import AoProject
from app.models.document import AoDocument
from app.core.security import hash_password, create_access_token

# ── Helpers ────────────────────────────────────────────────────────────────
def _make_headers(user_id: str, org_id: str, role: str = "admin") -> dict:
    """Crée un Bearer token de test."""
    token = create_access_token({"sub": user_id, "org_id": org_id, "role": role})
    return {"Authorization": f"Bearer {token}"}
async def _create_org_user_project(db: AsyncSession, plan: str = "starter", quota: int = 15):
    """Crée une org + user admin + projet pour les tests."""
    org = Organization(
        id=uuid.uuid4(),
        name=f"Test Org {uuid.uuid4().hex[:6]}",
        slug=f"test-org-{uuid.uuid4().hex[:6]}",
        plan=plan,
        quota_docs=quota,
    )
    db.add(org)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=f"user-{uuid.uuid4().hex[:6]}@test.com",
        hashed_pw=hash_password("TestPass123!"),
        role="admin",
        full_name="Test User",
    )
    db.add(user)
    await db.flush()

    project = AoProject(
        id=uuid.uuid4(),
        org_id=org.id,
        created_by=user.id,
        title="Projet Test Upload",
        status="draft",
    )
    db.add(project)
    await db.flush()

    return org, user, project
# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client_with_db(db_session):
    """Client HTTP avec override DB + mocks storage/celery."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    storage_mock = MagicMock()
    storage_mock.generate_s3_key.return_value = "org/proj/test.pdf"
    storage_mock.upload_bytes.return_value = None
    storage_mock.delete_object.return_value = None

    celery_task_mock = MagicMock()
    celery_task_mock.id = "test-celery-task-id"

    with patch("app.api.v1.documents.storage_service", storage_mock), \
         patch("app.worker.tasks.process_document") as mock_process:
        mock_process.delay.return_value = celery_task_mock

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac, db_session, storage_mock

    app.dependency_overrides.clear()
# ── Tests ──────────────────────────────────────────────────────────────────
class TestUploadValidPDF:
    """Upload d'un PDF valide — doit retourner 201."""

    
    async def test_upload_valid_pdf(self, client_with_db):
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)
        headers = _make_headers(str(user.id), str(org.id))

        pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("test_document.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["original_name"] == "test_document.pdf"
        assert data["status"] == "pending"

    
    async def test_upload_detects_doc_type_from_filename(self, client_with_db):
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)
        headers = _make_headers(str(user.id), str(org.id))

        pdf_content = b"%PDF-1.4 dummy content"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("CCTP_lot1.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 201
        assert response.json()["doc_type"] == "CCTP"
class TestMagicBytesValidation:
    """Validation des magic bytes PDF — protège contre les fichiers malveillants."""

    
    async def test_reject_fake_pdf_extension_only(self, client_with_db):
        """Fichier .pdf dont le contenu n'est pas un PDF — doit être rejeté."""
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)
        headers = _make_headers(str(user.id), str(org.id))

        # Contenu exe renommé en .pdf — sans magic bytes %PDF
        fake_content = b"MZ\x90\x00\x03\x00\x00\x00fake exe content"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("malware.pdf", fake_content, "application/pdf")},
        )
        assert response.status_code == 400
        assert "PDF valide" in response.json()["detail"]

    
    async def test_reject_non_pdf_extension(self, client_with_db):
        """Fichier .docx — doit être rejeté avant vérification magic bytes."""
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)
        headers = _make_headers(str(user.id), str(org.id))

        content = b"%PDF-1.4 tricky"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("document.docx", content, "application/pdf")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    
    async def test_reject_oversized_file(self, client_with_db):
        """Fichier > 50 Mo — doit être rejeté (HTTP 400)."""
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)
        headers = _make_headers(str(user.id), str(org.id))

        # Créer un contenu faussement lourd (51 Mo)
        large_content = b"%PDF-1.4 " + b"x" * (51 * 1024 * 1024)
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("big_file.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 400
        assert "volumineux" in response.json()["detail"]
class TestQuotaEnforcement:
    """Quota mensuel de documents — doit bloquer à quota_docs atteint."""

    
    async def test_quota_exceeded_returns_429(self, client_with_db):
        """Quand le quota est atteint, l'upload doit retourner 429."""
        client, db, _ = client_with_db
        # Org avec quota de 2 documents
        org, user, project = await _create_org_user_project(db, quota=2)
        headers = _make_headers(str(user.id), str(org.id))

        # Insérer 2 documents existants en BD pour simuler le quota atteint
        for i in range(2):
            doc = AoDocument(
                id=uuid.uuid4(),
                project_id=project.id,
                original_name=f"existing_{i}.pdf",
                s3_key=f"org/proj/existing_{i}.pdf",
                doc_type="AUTRES",
                status="done",
            )
            db.add(doc)
        await db.flush()

        pdf_content = b"%PDF-1.4 new upload attempt"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("new_doc.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 429
        assert "Quota" in response.json()["detail"]

    
    async def test_upload_allowed_under_quota(self, client_with_db):
        """Sous le quota, l'upload doit réussir."""
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db, quota=15)
        headers = _make_headers(str(user.id), str(org.id))

        # 1 document existant — quota de 15 donc largement OK
        doc = AoDocument(
            id=uuid.uuid4(),
            project_id=project.id,
            original_name="existing.pdf",
            s3_key="org/proj/existing.pdf",
            doc_type="AUTRES",
            status="done",
        )
        db.add(doc)
        await db.flush()

        pdf_content = b"%PDF-1.4 valid content"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            headers=headers,
            files={"file": ("allowed.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 201
class TestMultiTenantIsolation:
    """Isolation multi-tenant — org A ne peut pas voir/modifier les docs de org B."""

    
    async def test_cannot_upload_to_other_org_project(self, client_with_db):
        """Upload vers un projet d'une autre org doit retourner 404 (pas 403)."""
        client, db, _ = client_with_db

        # Org A + Org B
        org_a, user_a, project_a = await _create_org_user_project(db)
        org_b, user_b, project_b = await _create_org_user_project(db)

        # user_b essaie d'uploader sur project_a
        headers_b = _make_headers(str(user_b.id), str(org_b.id))
        pdf_content = b"%PDF-1.4 unauthorized"
        response = await client.post(
            f"/api/v1/projects/{project_a.id}/documents/upload",
            headers=headers_b,
            files={"file": ("attack.pdf", pdf_content, "application/pdf")},
        )
        # Doit retourner 404 — on ne révèle pas l'existence du projet
        assert response.status_code == 404

    
    async def test_list_documents_only_own_org(self, client_with_db):
        """Lister les documents d'un projet appartenant à une autre org → 404."""
        client, db, _ = client_with_db

        org_a, user_a, project_a = await _create_org_user_project(db)
        org_b, user_b, project_b = await _create_org_user_project(db)

        # Ajouter un doc dans project_a
        doc = AoDocument(
            id=uuid.uuid4(),
            project_id=project_a.id,
            original_name="secret.pdf",
            s3_key="org_a/proj/secret.pdf",
            doc_type="RC",
            status="done",
        )
        db.add(doc)
        await db.flush()

        # user_b liste les docs de project_a
        headers_b = _make_headers(str(user_b.id), str(org_b.id))
        response = await client.get(
            f"/api/v1/projects/{project_a.id}/documents",
            headers=headers_b,
        )
        assert response.status_code == 404
class TestUnauthenticatedAccess:
    """Accès sans token JWT — doit retourner 401/403."""

    
    async def test_upload_without_token(self, client_with_db):
        client, db, _ = client_with_db
        org, user, project = await _create_org_user_project(db)

        pdf_content = b"%PDF-1.4 no auth"
        response = await client.post(
            f"/api/v1/projects/{project.id}/documents/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code in (401, 403)
