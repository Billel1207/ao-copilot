"""Tests pour le pipeline d'analyse IA (avec LLM et embedder mockés)."""
import pytest
from unittest.mock import patch, MagicMock
# ── Helpers ────────────────────────────────────────────────────────────────

async def register_and_login(client, email="analyst@test.fr", org="Org Analyst"):
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Analyst",
        "org_name": org,
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "SecurePass123!",
    })
    return resp.json()["access_token"]
def auth(token):
    return {"Authorization": f"Bearer {token}"}
async def create_project(client, token, title="Projet Test Analyse"):
    resp = await client.post(
        "/api/v1/projects",
        json={"title": title, "buyer": "Mairie Test", "market_type": "travaux"},
        headers=auth(token),
    )
    return resp.json()["id"]
# ── Tests ──────────────────────────────────────────────────────────────────
async def test_trigger_analysis_returns_task_id(client, mock_celery):
    """POST /analyze → 202 + task_id."""
    token = await register_and_login(client)
    project_id = await create_project(client, token)

    resp = await client.post(
        f"/api/v1/projects/{project_id}/analyze",
        headers=auth(token),
    )
    assert resp.status_code == 202, resp.text
    data = resp.json()
    assert "task_id" in data
    assert data["project_id"] == project_id

async def test_get_status_returns_progress(client, mock_celery):
    """
    GET /analyze/status renvoie progress_pct réel depuis Redis.
    Valide le fix C1 : lecture Redis au lieu de hardcoded 50.
    """
    token = await register_and_login(client, email="status@test.fr", org="Org Status")
    project_id = await create_project(client, token)

    # Lancer l'analyse
    await client.post(
        f"/api/v1/projects/{project_id}/analyze",
        headers=auth(token),
    )

    # Mock Redis get pour simuler une progression réelle
    mock_redis = MagicMock()
    mock_redis.get.side_effect = lambda key: (
        "test-task-id-12345" if "project_task" in key
        else '{"pct":75,"step":"Génération checklist"}'
    )

    with patch("app.api.v1.analysis.get_redis", return_value=mock_redis):
        resp = await client.get(
            f"/api/v1/projects/{project_id}/analyze/status",
            headers=auth(token),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["progress_pct"] == 75
    assert data["current_step"] == "Génération checklist"
    assert data["status"] == "analyzing"

async def test_get_checklist_with_filters(client, db_session):
    """GET /checklist avec filtres criticality et status."""
    from app.models.analysis import ChecklistItem
    from app.models.project import AoProject
    from app.models.organization import Organization
    from app.models.user import User
    import uuid

    token = await register_and_login(client, email="checklist@test.fr", org="Org Checklist")
    project_id = await create_project(client, token)

    # Insérer des items de checklist directement en DB
    pid = uuid.UUID(project_id)
    items_data = [
        ChecklistItem(
            project_id=pid,
            category="Administratif",
            requirement="DC1",
            criticality="Éliminatoire",
            status="MANQUANT",
            citations=[],
        ),
        ChecklistItem(
            project_id=pid,
            category="Technique",
            requirement="Référence chantier",
            criticality="Important",
            status="OK",
            citations=[],
        ),
    ]
    for item in items_data:
        db_session.add(item)
    await db_session.flush()

    # Filtrer par criticality
    resp = await client.get(
        f"/api/v1/projects/{project_id}/checklist",
        params={"criticality": "Éliminatoire"},
        headers=auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2  # total = tous les items
    assert len(data["checklist"]) == 1  # filtré
    assert data["checklist"][0]["criticality"] == "Éliminatoire"

    # Filtrer par status
    resp2 = await client.get(
        f"/api/v1/projects/{project_id}/checklist",
        params={"status": "OK"},
        headers=auth(token),
    )
    assert resp2.status_code == 200
    assert len(resp2.json()["checklist"]) == 1
    assert resp2.json()["checklist"][0]["status"] == "OK"

async def test_get_summary_not_available_before_analysis(client):
    """GET /summary avant analyse → 404."""
    token = await register_and_login(client, email="summary@test.fr", org="Org Summary")
    project_id = await create_project(client, token)

    resp = await client.get(
        f"/api/v1/projects/{project_id}/summary",
        headers=auth(token),
    )
    assert resp.status_code == 404
    assert "lancez l'analyse" in resp.json()["detail"]
