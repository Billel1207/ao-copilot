"""Fixtures pytest pour la suite de tests AO Copilot."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

import app.database as app_db
from app.database import Base


# ── Base de données de test (PostgreSQL du CI ou SQLite fallback) ──────────

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def engine():
    """Moteur DB pour les tests — PostgreSQL en CI, SQLite en local.

    Remplace aussi le moteur global dans app.database pour éviter
    les conflits d'event loop (l'engine module-level est créé à l'import
    dans un loop différent du loop de test session).
    """
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Créer les tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Monkey-patch l'engine et la session factory globales
    original_engine = app_db.engine
    original_session = app_db.AsyncSessionLocal

    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    app_db.engine = test_engine
    app_db.AsyncSessionLocal = test_session_factory

    yield test_engine

    # Restaurer
    app_db.engine = original_engine
    app_db.AsyncSessionLocal = original_session

    # Nettoyage
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(engine):
    """Session de DB isolée par test — rollback automatique après chaque test."""
    TestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def client(db_session):
    """Client HTTP de test avec override de la dépendance DB."""
    from app.main import app
    from app.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Mock LLM — retourne du JSON fixe pour tous les appels ──────────────────
MOCK_SUMMARY = {
    "project_overview": {
        "scope": "Construction de 10 logements sociaux",
        "buyer": "Mairie de Test",
        "location": "Paris 75001",
        "deadline_submission": "2026-04-01",
        "estimated_budget": "500 000 €",
    },
    "key_points": [
        {"label": "Budget", "value": "500 000 €", "citations": []},
    ],
    "risks": [
        {"risk": "Délai serré", "severity": "medium", "why": "3 mois seulement"},
    ],
    "actions_next_48h": [
        {"action": "Vérifier attestations", "owner_role": "Directeur", "priority": "P0"},
    ],
}

MOCK_CHECKLIST = {
    "checklist": [
        {
            "category": "Administratif",
            "requirement": "DC1 signé",
            "criticality": "Éliminatoire",
            "status": "MANQUANT",
            "what_to_provide": "DC1 signé par le représentant légal",
            "citations": [],
            "confidence": 0.95,
        }
    ]
}

MOCK_CRITERIA = {
    "evaluation": {
        "eligibility_conditions": [
            {"condition": "CA > 1M€", "type": "hard", "citations": []}
        ],
        "scoring_criteria": [
            {"criterion": "Prix", "weight_percent": 60, "notes": "Sur 10 points", "citations": []}
        ],
    }
}


@pytest.fixture
def mock_llm():
    """Patch LLMService.complete_json pour retourner du JSON prédéfini selon le contexte."""
    call_count = {"n": 0}

    def side_effect(system_prompt, user_prompt, json_schema=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MOCK_SUMMARY
        elif call_count["n"] == 2:
            return MOCK_CHECKLIST
        else:
            return MOCK_CRITERIA

    with patch("app.services.llm.llm_service.complete_json", side_effect=side_effect):
        yield


@pytest.fixture
def mock_storage():
    """Patch StorageService pour éviter les appels MinIO."""
    with patch("app.services.storage.storage_service") as mock:
        mock.upload_file = MagicMock(return_value="documents/test/test.pdf")
        mock.get_signed_url = MagicMock(return_value="http://minio/signed/test.pdf")
        mock.download_bytes = MagicMock(return_value=b"%PDF-1.4 fake pdf content")
        mock.delete_file = MagicMock(return_value=True)
        yield mock


@pytest.fixture
def mock_embedder():
    """Patch embed_texts et embed_query pour éviter les appels OpenAI."""
    fake_embedding = [0.1] * 1536
    with patch("app.services.embedder.embed_texts", return_value=[fake_embedding]), \
         patch("app.services.embedder.embed_query", return_value=fake_embedding):
        yield


@pytest.fixture
def mock_celery():
    """Patch les tâches Celery pour les exécuter de façon synchrone."""
    task_mock = MagicMock()
    task_mock.id = "test-task-id-12345"
    with patch("app.worker.tasks.process_document.delay", return_value=task_mock), \
         patch("app.worker.tasks.analyze_project.delay", return_value=task_mock):
        yield task_mock
