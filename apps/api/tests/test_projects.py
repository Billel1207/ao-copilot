"""Tests pour le CRUD des projets (isolation org, archive, etc.)."""
import pytest
# ── Helpers ────────────────────────────────────────────────────────────────

async def register_and_login(client, email="user@test.fr", org="Org Test"):
    """Inscrit un user et retourne son access_token."""
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Test User",
        "org_name": org,
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "SecurePass123!",
    })
    return resp.json()["access_token"]
def auth(token):
    return {"Authorization": f"Bearer {token}"}
PROJECT_DATA = {
    "title": "Appel d'offres Travaux RN7",
    "reference": "AO-2026-001",
    "buyer": "DIR Méditerranée",
    "market_type": "travaux",
}
# ── Tests ──────────────────────────────────────────────────────────────────
async def test_create_project(client):
    """Création d'un projet → 201 + champs corrects."""
    token = await register_and_login(client)
    resp = await client.post("/api/v1/projects", json=PROJECT_DATA, headers=auth(token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == PROJECT_DATA["title"]
    assert data["status"] == "draft"
    assert "id" in data
    assert "org_id" in data

async def test_list_projects_only_own_org(client):
    """Un utilisateur ne voit pas les projets d'une autre organisation."""
    token_a = await register_and_login(client, email="a@test.fr", org="Org A")
    token_b = await register_and_login(client, email="b@test.fr", org="Org B")

    # A crée un projet
    await client.post("/api/v1/projects", json=PROJECT_DATA, headers=auth(token_a))

    # B ne doit pas voir le projet de A
    resp = await client.get("/api/v1/projects", headers=auth(token_b))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []

async def test_get_project_not_found_returns_404(client):
    """GET sur un UUID inexistant → 404."""
    token = await register_and_login(client, email="c@test.fr", org="Org C")
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/projects/{fake_id}", headers=auth(token))
    assert resp.status_code == 404

async def test_update_project(client):
    """PATCH met à jour les champs autorisés."""
    token = await register_and_login(client, email="d@test.fr", org="Org D")
    create_resp = await client.post("/api/v1/projects", json=PROJECT_DATA, headers=auth(token))
    project_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"title": "Titre modifié"},
        headers=auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Titre modifié"

async def test_archive_project_persists(client):
    """
    DELETE (archive) d'un projet → status='archived' persisté en DB.
    Valide le fix A1 : await db.commit() dans archive_project().
    """
    token = await register_and_login(client, email="e@test.fr", org="Org E")
    create_resp = await client.post("/api/v1/projects", json=PROJECT_DATA, headers=auth(token))
    project_id = create_resp.json()["id"]

    # Archiver
    del_resp = await client.delete(f"/api/v1/projects/{project_id}", headers=auth(token))
    assert del_resp.status_code == 204

    # Vérifier que le projet est bien archivé (status filtre)
    list_resp = await client.get(
        "/api/v1/projects",
        params={"status": "archived"},
        headers=auth(token),
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(p["id"] == project_id for p in items), "Projet archivé non trouvé en DB"
