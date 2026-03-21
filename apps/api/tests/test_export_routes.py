"""Tests pour les routes d'export (PDF, Word, DPGF Excel, Memo, Pack).

Couvre : autorisation, vérification plan, projet introuvable, statut non-ready,
appels Celery mockés, vérification de statut d'export.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from app.models.project import AoProject
from app.models.organization import Organization
from app.models.user import User
from app.core.security import hash_password, create_access_token


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_test_context(db_session, plan="pro", project_status="ready"):
    """Create org + user + project in DB, return (org, user, project, token, headers)."""
    org = Organization(
        name="Export Test Org",
        slug=f"export-test-{uuid.uuid4().hex[:8]}",
        plan=plan,
        quota_docs=50,
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        org_id=org.id,
        email=f"export-{uuid.uuid4().hex[:6]}@test.fr",
        hashed_pw=hash_password("TestPass123!"),
        full_name="Export Tester",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()

    project = AoProject(
        org_id=org.id,
        created_by=user.id,
        title="Projet Export Test",
        status=project_status,
    )
    db_session.add(project)
    await db_session.flush()

    token_data = {"sub": str(user.id), "org_id": str(org.id), "role": user.role}
    token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {token}"}

    return org, user, project, token, headers


# ── PDF Export ───────────────────────────────────────────────────────────────

async def test_export_pdf_success(client, db_session):
    """POST /export/pdf with ready project -> launches Celery task."""
    _, _, project, _, headers = await _create_test_context(db_session)

    task_mock = MagicMock()
    task_mock.id = "pdf-task-123"

    with patch("app.worker.tasks.export_project_pdf") as mock_task:
        mock_task.delay.return_value = task_mock
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/pdf",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "pdf-task-123"
    assert data["status"] == "pending"


async def test_export_pdf_project_not_found(client, db_session):
    """PDF export for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session)
    fake_id = uuid.uuid4()

    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/pdf",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_export_pdf_not_ready(client, db_session):
    """PDF export for draft project -> 400."""
    _, _, project, _, headers = await _create_test_context(db_session, project_status="draft")

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/pdf",
        headers=headers,
    )
    assert resp.status_code == 400
    assert "ready" in resp.json()["detail"].lower()


async def test_export_pdf_unauthorized(client, db_session):
    """PDF export without auth -> 401."""
    _, _, project, _, _ = await _create_test_context(db_session)
    resp = await client.post(f"/api/v1/projects/{project.id}/export/pdf")
    assert resp.status_code in (401, 403)


# ── Word Export ──────────────────────────────────────────────────────────────

async def test_export_word_success_pro_plan(client, db_session):
    """Word export on pro plan -> success."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")

    task_mock = MagicMock()
    task_mock.id = "docx-task-456"

    with patch("app.worker.tasks.export_project_docx") as mock_task:
        mock_task.delay.return_value = task_mock
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/word",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "docx-task-456"


async def test_export_word_forbidden_free_plan(client, db_session):
    """Word export on free plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="free")

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/word",
        headers=headers,
    )
    assert resp.status_code == 403
    assert "pro" in resp.json()["detail"].lower()


async def test_export_word_forbidden_starter_plan(client, db_session):
    """Word export on starter plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="starter")

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/word",
        headers=headers,
    )
    assert resp.status_code == 403


# ── Memo Export ──────────────────────────────────────────────────────────────

async def test_export_memo_forbidden_free_plan(client, db_session):
    """Memo export on free plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="free")

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/memo",
        headers=headers,
    )
    assert resp.status_code == 403


async def test_export_memo_project_not_found(client, db_session):
    """Memo export for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session, plan="pro")
    fake_id = uuid.uuid4()

    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/memo",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_export_memo_not_ready(client, db_session):
    """Memo export for analyzing project -> 400."""
    _, _, project, _, headers = await _create_test_context(
        db_session, plan="pro", project_status="analyzing"
    )

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/memo",
        headers=headers,
    )
    assert resp.status_code == 400


async def test_export_memo_success(client, db_session):
    """Memo export success dispatches Celery job and returns job_id."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")

    mock_task = MagicMock()
    mock_task.id = "test-task-id-123"

    with patch("app.worker.tasks.export_project_memo") as mock_export:
        mock_export.delay.return_value = mock_task
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/memo",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "test-task-id-123"
    assert data["status"] == "pending"
    mock_export.delay.assert_called_once_with(str(project.id))


# ── Pack Export ──────────────────────────────────────────────────────────────

async def test_export_pack_forbidden_free_plan(client, db_session):
    """Pack export on free plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="free")

    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/pack",
        headers=headers,
    )
    assert resp.status_code == 403


async def test_export_pack_success(client, db_session):
    """Pack export on pro plan -> launches Celery task."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")

    task_mock = MagicMock()
    task_mock.id = "pack-task-789"

    with patch("app.worker.tasks.export_project_pack") as mock_task:
        mock_task.delay.return_value = task_mock
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/pack",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "pack-task-789"


# ── Export status ────────────────────────────────────────────────────────────

async def test_export_status_pending(client, db_session):
    """GET export status for pending task."""
    _, _, project, _, headers = await _create_test_context(db_session)

    mock_result = MagicMock()
    mock_result.state = "PENDING"

    with patch("app.worker.celery_app.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = await client.get(
            f"/api/v1/projects/{project.id}/export/some-job-id",
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


async def test_export_status_success(client, db_session):
    """GET export status for completed task returns download URL."""
    _, _, project, _, headers = await _create_test_context(db_session)

    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    mock_result.result = "exports/test/file.pdf"

    with patch("app.worker.celery_app.celery_app") as mock_celery, \
         patch("app.services.storage.storage_service") as mock_storage:
        mock_celery.AsyncResult.return_value = mock_result
        mock_storage.get_signed_download_url.return_value = "https://s3.example.com/signed"
        resp = await client.get(
            f"/api/v1/projects/{project.id}/export/some-job-id",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert "url" in data


async def test_export_status_failure(client, db_session):
    """GET export status for failed task returns error."""
    _, _, project, _, headers = await _create_test_context(db_session)

    mock_result = MagicMock()
    mock_result.state = "FAILURE"
    mock_result.info = Exception("Generation failed")

    with patch("app.worker.celery_app.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = await client.get(
            f"/api/v1/projects/{project.id}/export/some-job-id",
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
