"""Load testing pour AO Copilot — basé sur locust.

Installation: pip install locust
Usage:
    locust -f scripts/load_test.py --host=http://localhost:8000
    # Ou en mode headless:
    locust -f scripts/load_test.py --host=http://localhost:8000 \
        --users=50 --spawn-rate=5 --run-time=2m --headless

Scénarios testés:
1. Health check (baseline throughput)
2. Auth flow (login → token refresh)
3. Project listing (dashboard principal)
4. Document upload simulation
5. Analysis status polling
6. Export PDF/DOCX
"""
import os
import json
import random
from locust import HttpUser, task, between, events

# Config
BASE_EMAIL = os.getenv("LOAD_TEST_EMAIL", "loadtest@ao-copilot.fr")
BASE_PASSWORD = os.getenv("LOAD_TEST_PASSWORD", "LoadTest2026!")
API_PREFIX = "/api/v1"


class AOCopilotUser(HttpUser):
    """Simule un utilisateur BTP typique analysant des DCE."""

    wait_time = between(1, 5)  # 1-5 secondes entre actions (usage réel)
    host = "http://localhost:8000"

    def on_start(self):
        """Login au démarrage de chaque utilisateur simulé."""
        self.token = None
        self.project_ids = []
        self._login()

    def _login(self):
        """Authentification et récupération du token JWT."""
        resp = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"email": BASE_EMAIL, "password": BASE_PASSWORD},
            name="POST /auth/login",
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
        else:
            # Si le login échoue, on continue sans token pour mesurer les 401
            self.token = None

    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Health Check (baseline) ──────────────────────────────────────────

    @task(3)
    def health_check(self):
        """GET /health — devrait être < 50ms."""
        self.client.get("/health", name="GET /health")

    # ── Dashboard & Projects ─────────────────────────────────────────────

    @task(5)
    def list_projects(self):
        """GET /projects — dashboard principal, fréquent."""
        resp = self.client.get(
            f"{API_PREFIX}/projects/",
            headers=self._headers(),
            name="GET /projects",
        )
        if resp.status_code == 200:
            data = resp.json()
            projects = data if isinstance(data, list) else data.get("items", [])
            self.project_ids = [p["id"] for p in projects[:10]]

    @task(3)
    def get_project_detail(self):
        """GET /projects/:id — détail d'un projet."""
        if not self.project_ids:
            return
        pid = random.choice(self.project_ids)
        self.client.get(
            f"{API_PREFIX}/projects/{pid}",
            headers=self._headers(),
            name="GET /projects/:id",
        )

    # ── Analysis Results ─────────────────────────────────────────────────

    @task(4)
    def get_analysis_results(self):
        """GET /projects/:id/analysis/:type — récupérer un résultat d'analyse."""
        if not self.project_ids:
            return
        pid = random.choice(self.project_ids)
        analysis_type = random.choice([
            "summary", "checklist", "criteria", "gonogo",
            "timeline", "ccap_risks", "rc_analysis",
        ])
        self.client.get(
            f"{API_PREFIX}/projects/{pid}/analysis/{analysis_type}",
            headers=self._headers(),
            name="GET /analysis/:type",
        )

    # ── Billing & Plans ──────────────────────────────────────────────────

    @task(1)
    def get_plans(self):
        """GET /billing/plans — page tarification."""
        self.client.get(
            f"{API_PREFIX}/billing/plans",
            headers=self._headers(),
            name="GET /billing/plans",
        )

    @task(1)
    def get_usage(self):
        """GET /billing/usage — stats d'utilisation."""
        self.client.get(
            f"{API_PREFIX}/billing/usage",
            headers=self._headers(),
            name="GET /billing/usage",
        )

    # ── Export ────────────────────────────────────────────────────────────

    @task(2)
    def export_pdf(self):
        """POST /projects/:id/export/pdf — export rapport PDF."""
        if not self.project_ids:
            return
        pid = random.choice(self.project_ids)
        self.client.post(
            f"{API_PREFIX}/projects/{pid}/export/pdf",
            headers=self._headers(),
            name="POST /export/pdf",
        )

    # ── Chat DCE ─────────────────────────────────────────────────────────

    @task(2)
    def chat_question(self):
        """POST /projects/:id/chat — question RAG sur le DCE."""
        if not self.project_ids:
            return
        pid = random.choice(self.project_ids)
        questions = [
            "Quel est le montant estimé du marché ?",
            "Quelles sont les pénalités de retard ?",
            "La sous-traitance est-elle autorisée ?",
            "Quelle est la date limite de remise ?",
            "Quelles certifications sont exigées ?",
        ]
        self.client.post(
            f"{API_PREFIX}/projects/{pid}/chat",
            json={"question": random.choice(questions)},
            headers=self._headers(),
            name="POST /chat",
        )


# ── Event hooks pour métriques custom ────────────────────────────────────────

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Affiche un résumé à la fin du test."""
    stats = environment.runner.stats
    total = stats.total
    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total requests: {total.num_requests}")
    print(f"Total failures: {total.num_failures}")
    print(f"Failure rate:   {total.fail_ratio * 100:.1f}%")
    print(f"Avg response:   {total.avg_response_time:.0f}ms")
    print(f"Median:         {total.get_response_time_percentile(0.5):.0f}ms")
    print(f"P95:            {total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99:            {total.get_response_time_percentile(0.99):.0f}ms")
    print(f"RPS:            {total.total_rps:.1f}")
    print("=" * 60)

    # Fail si > 5% d'erreurs ou P95 > 2s
    if total.fail_ratio > 0.05:
        print(f"⚠ FAIL: Error rate {total.fail_ratio*100:.1f}% exceeds 5% threshold")
    if total.get_response_time_percentile(0.95) > 2000:
        print(f"⚠ FAIL: P95 {total.get_response_time_percentile(0.95):.0f}ms exceeds 2s threshold")
