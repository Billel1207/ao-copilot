"""Extended tests for export routes — DPGF Excel, Analysis Excel, edge cases.

Covers endpoints and scenarios not covered by test_export_routes.py.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.organization import Organization
from app.models.user import User
from app.core.security import hash_password, create_access_token


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_test_context(db_session, plan="pro", project_status="ready"):
    """Create org + user + project in DB."""
    org = Organization(
        name="Export Ext Test Org",
        slug=f"export-ext-{uuid.uuid4().hex[:8]}",
        plan=plan,
        quota_docs=50,
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        org_id=org.id,
        email=f"export-ext-{uuid.uuid4().hex[:6]}@test.fr",
        hashed_pw=hash_password("TestPass123!"),
        full_name="Export Ext Tester",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()

    project = AoProject(
        org_id=org.id,
        created_by=user.id,
        title="Projet Export Extended Test",
        status=project_status,
    )
    db_session.add(project)
    await db_session.flush()

    token_data = {"sub": str(user.id), "org_id": str(org.id), "role": user.role}
    token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {token}"}

    return org, user, project, token, headers


# ── DPGF Excel Export ────────────────────────────────────────────────────────

async def test_export_dpgf_excel_forbidden_free(client, db_session):
    """DPGF Excel on free plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="free")
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
    )
    assert resp.status_code == 403
    assert "pro" in resp.json()["detail"].lower()


async def test_export_dpgf_excel_forbidden_starter(client, db_session):
    """DPGF Excel on starter plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="starter")
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
    )
    assert resp.status_code == 403


async def test_export_dpgf_excel_project_not_found(client, db_session):
    """DPGF Excel for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session, plan="pro")
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/dpgf-excel", headers=headers,
    )
    assert resp.status_code == 404


async def test_export_dpgf_excel_not_ready(client, db_session):
    """DPGF Excel for draft project -> 400."""
    _, _, project, _, headers = await _create_test_context(
        db_session, plan="pro", project_status="analyzing"
    )
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
    )
    assert resp.status_code == 400


async def test_export_dpgf_excel_no_documents(client, db_session):
    """DPGF Excel when no DPGF/BPU docs exist -> 404."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
    )
    assert resp.status_code == 404
    assert "dpgf" in resp.json()["detail"].lower() or "bpu" in resp.json()["detail"].lower()


async def test_export_dpgf_excel_success(client, db_session):
    """DPGF Excel with valid DPGF document -> 200 with xlsx response."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")

    doc = AoDocument(
        project_id=project.id,
        original_name="DPGF_test.pdf",
        s3_key="docs/dpgf_test.pdf",
        doc_type="DPGF",
        status="done",
    )
    db_session.add(doc)
    await db_session.flush()

    fake_tables = [{"col1": "val1"}]
    fake_excel = b"PK\x03\x04"  # fake xlsx bytes

    with patch("app.services.storage.storage_service") as mock_storage, \
         patch("app.services.dpgf_extractor.extract_tables_from_pdf", return_value=fake_tables), \
         patch("app.services.dpgf_extractor.generate_excel", return_value=fake_excel):
        mock_storage.download_bytes.return_value = b"%PDF-1.4 fake"
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
        )

    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers.get("content-type", "")
    assert "DPGF_" in resp.headers.get("content-disposition", "")


async def test_export_dpgf_excel_doc_extraction_error(client, db_session):
    """DPGF Excel when one doc fails extraction -> still returns result from others."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="pro")

    # Two docs: one will fail, one will succeed
    doc1 = AoDocument(
        project_id=project.id,
        original_name="DPGF_fail.pdf",
        s3_key="docs/dpgf_fail.pdf",
        doc_type="DPGF",
        status="done",
    )
    doc2 = AoDocument(
        project_id=project.id,
        original_name="BPU_ok.pdf",
        s3_key="docs/bpu_ok.pdf",
        doc_type="BPU",
        status="done",
    )
    db_session.add(doc1)
    db_session.add(doc2)
    await db_session.flush()

    call_count = {"n": 0}

    def side_effect_download(key):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("S3 download failed")
        return b"%PDF-1.4 fake"

    fake_excel = b"PK\x03\x04"

    mock_logger = MagicMock()
    with patch("app.services.storage.storage_service") as mock_storage, \
         patch("app.services.dpgf_extractor.extract_tables_from_pdf", return_value=[{"a": "b"}]), \
         patch("app.services.dpgf_extractor.generate_excel", return_value=fake_excel), \
         patch("logging.getLogger", return_value=mock_logger):
        mock_storage.download_bytes.side_effect = side_effect_download
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/dpgf-excel", headers=headers,
        )

    assert resp.status_code == 200


# ── Analysis Excel Export ────────────────────────────────────────────────────

async def test_export_analysis_excel_forbidden_free(client, db_session):
    """Analysis Excel on free plan -> 403."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="free")
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/analysis-excel", headers=headers,
    )
    assert resp.status_code == 403


async def test_export_analysis_excel_project_not_found(client, db_session):
    """Analysis Excel for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session, plan="pro")
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/analysis-excel", headers=headers,
    )
    assert resp.status_code == 404


async def test_export_analysis_excel_not_ready(client, db_session):
    """Analysis Excel for draft project -> 400."""
    _, _, project, _, headers = await _create_test_context(
        db_session, plan="pro", project_status="draft"
    )
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/analysis-excel", headers=headers,
    )
    assert resp.status_code == 400


async def test_export_analysis_excel_success(client, db_session):
    """Analysis Excel with valid project -> 200 with xlsx response."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="europe")

    fake_excel = b"PK\x03\x04"

    with patch("app.services.excel_exporter.generate_analysis_excel", return_value=fake_excel), \
         patch("app.core.database.SyncSessionLocal") as mock_sync:
        mock_session = MagicMock()
        mock_sync.return_value = mock_session
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/analysis-excel", headers=headers,
        )

    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers.get("content-type", "")
    mock_session.close.assert_called_once()


# ── Export status edge cases ─────────────────────────────────────────────────

async def test_export_status_started(client, db_session):
    """GET export status for STARTED task -> processing."""
    _, _, project, _, headers = await _create_test_context(db_session)

    mock_result = MagicMock()
    mock_result.state = "STARTED"

    with patch("app.worker.celery_app.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = await client.get(
            f"/api/v1/projects/{project.id}/export/some-job-id",
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"
    assert resp.json()["progress"] == 50


async def test_export_status_unknown_state(client, db_session):
    """GET export status for unknown Celery state -> lowercased state name."""
    _, _, project, _, headers = await _create_test_context(db_session)

    mock_result = MagicMock()
    mock_result.state = "RETRY"

    with patch("app.worker.celery_app.celery_app") as mock_celery:
        mock_celery.AsyncResult.return_value = mock_result
        resp = await client.get(
            f"/api/v1/projects/{project.id}/export/some-job-id",
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "retry"


# ── Pack export additional tests ─────────────────────────────────────────────

async def test_export_pack_not_ready(client, db_session):
    """Pack export for not-ready project -> 400."""
    _, _, project, _, headers = await _create_test_context(
        db_session, plan="pro", project_status="analyzing"
    )
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/pack", headers=headers,
    )
    assert resp.status_code == 400


async def test_export_pack_project_not_found(client, db_session):
    """Pack export for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session, plan="business")
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/pack", headers=headers,
    )
    assert resp.status_code == 404


# ── Word export on trial plan ───────────────────────────────────────────────

async def test_export_word_allowed_trial_plan(client, db_session):
    """Word export on trial plan -> success (trial has Pro features)."""
    _, _, project, _, headers = await _create_test_context(db_session, plan="trial")

    task_mock = MagicMock()
    task_mock.id = "docx-trial-123"

    with patch("app.worker.tasks.export_project_docx") as mock_task:
        mock_task.delay.return_value = task_mock
        resp = await client.post(
            f"/api/v1/projects/{project.id}/export/word", headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["job_id"] == "docx-trial-123"


async def test_export_word_project_not_found(client, db_session):
    """Word export for non-existent project -> 404."""
    _, _, _, _, headers = await _create_test_context(db_session, plan="pro")
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{fake_id}/export/word", headers=headers,
    )
    assert resp.status_code == 404


async def test_export_word_not_ready(client, db_session):
    """Word export for not-ready project -> 400."""
    _, _, project, _, headers = await _create_test_context(
        db_session, plan="pro", project_status="analyzing"
    )
    resp = await client.post(
        f"/api/v1/projects/{project.id}/export/word", headers=headers,
    )
    assert resp.status_code == 400
