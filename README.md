# AO Copilot

Micro-SaaS B2B d'analyse automatique de DCE (Dossiers de Consultation des Entreprises) pour les entreprises BTP et d'ingénierie françaises.

**Pipeline** : Upload PDF → OCR → Chunking → Embeddings → RAG → Claude (Anthropic) → Résumé + Checklist + Critères d'attribution

---

## Stack technique

| Couche | Technologie |
|--------|------------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + Zustand + React Query |
| Backend | FastAPI (Python 3.12) + Pydantic v2 + SQLAlchemy 2 |
| Queue | Celery + Redis |
| Base de données | PostgreSQL 16 + pgvector (embeddings 1536 dims) |
| Stockage | MinIO local (S3-compatible) → Scaleway en prod |
| IA | Anthropic Claude Sonnet 4.6 (analyse) + OpenAI text-embedding-3-small (embeddings) |
| OCR | PyMuPDF + Tesseract OCR (inclus dans Docker) |
| Export | WeasyPrint (PDF) |

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x
- [Node.js](https://nodejs.org/) ≥ 20.x
- Clé API Anthropic (analyse IA) + OpenAI (embeddings)

> Python 3.12 requis uniquement pour le **développement local sans Docker**.

---

## Installation rapide (Docker — recommandé)

### 1. Cloner et configurer l'environnement

```bash
git clone <repo>
cd ao-copilot

# Copier et remplir les variables d'environnement
cp .env.example .env
# Éditer .env : renseigner ANTHROPIC_API_KEY + OPENAI_API_KEY (embeddings) + SECRET_KEY
```

### 2. Démarrer tous les services Docker

```bash
# Démarre : postgres, redis, minio, api (FastAPI + Tesseract), worker (Celery)
docker compose up -d

# Vérifier que tout est UP
docker compose ps
```

### 3. Appliquer les migrations de base de données

```bash
docker compose exec api alembic upgrade head
```

### 4. Installer et démarrer le frontend

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

### 5. Accéder à l'application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Swagger** | http://localhost:8000/api/docs |
| **MinIO Console** | http://localhost:9001 |

---

## Installation dev local (sans Docker pour l'API)

Utile pour déboguer le backend avec hot-reload.

### 1. Démarrer uniquement l'infra

```bash
# Uniquement postgres, redis, minio
docker compose up -d postgres redis minio
```

### 2. Créer le venv Python et installer les dépendances

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Installer Tesseract OCR (requis pour l'OCR fallback)

**Windows** :
```powershell
winget install UB-Mannheim.TesseractOCR
# Puis ajouter C:\Program Files\Tesseract-OCR\ au PATH système
```

**macOS** :
```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian** :
```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

### 4. Appliquer les migrations

```bash
# Depuis apps/api (venv activé)
alembic upgrade head
```

### 5. Démarrer le backend et le worker

```bash
# Terminal 1 — API FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Celery Worker
python -m celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
```

### 6. Démarrer le frontend

```bash
cd apps/web && npm run dev
```

---

## Variables d'environnement

Copier `.env.example` → `.env` et renseigner :

| Variable | Description | Requis |
|----------|-------------|--------|
| `SECRET_KEY` | Clé JWT (min 32 chars, aléatoire) | ✅ |
| `ANTHROPIC_API_KEY` | Clé API Anthropic (analyse IA Claude) | ✅ |
| `OPENAI_API_KEY` | Clé API OpenAI (embeddings uniquement) | ✅ |
| `LLM_MODEL` | Modèle Claude (`claude-sonnet-4-6`) | ❌ (défaut ok) |
| `DATABASE_URL` | URL PostgreSQL (asyncpg) | ✅ |
| `DATABASE_URL_SYNC` | URL PostgreSQL (sync, pour Celery) | ✅ |
| `REDIS_URL` | URL Redis | ✅ |
| `S3_ENDPOINT_URL` | URL MinIO / S3 | ✅ |
| `S3_ACCESS_KEY` | Clé S3 | ✅ |
| `S3_SECRET_KEY` | Secret S3 | ✅ |
| `SENTRY_DSN` | DSN Sentry (optionnel) | ❌ |

---

## Architecture

```
ao-copilot/
├── apps/
│   ├── web/                        # Frontend Next.js 14 (port 3000)
│   │   ├── src/app/                # Pages (App Router)
│   │   │   ├── (auth)/             # Login / Register
│   │   │   └── (dashboard)/        # Dashboard, projets, upload
│   │   ├── src/components/         # Composants UI modulaires
│   │   ├── src/hooks/              # React Query hooks
│   │   ├── src/stores/             # Zustand auth store
│   │   └── src/lib/                # Axios client, utils
│   │
│   └── api/                        # Backend FastAPI (port 8000)
│       ├── app/
│       │   ├── api/v1/             # Routes REST
│       │   ├── models/             # SQLAlchemy ORM (multi-tenant)
│       │   ├── schemas/            # Pydantic v2
│       │   ├── services/           # LLM, PDF, RAG, Storage, Export
│       │   └── worker/             # Tâches Celery async
│       ├── alembic/                # Migrations PostgreSQL
│       ├── tests/                  # Suite de tests pytest
│       └── requirements.txt
├── scripts/                        # Lanceurs Node.js (dev Windows)
├── docker-compose.yml              # Infra complète (postgres/redis/minio/api/worker)
├── .env.example
└── README.md
```

---

## Pipeline IA

```
PDF Upload
    │
    ▼
PyMuPDF extraction ──► Tesseract OCR (fallback si <50 chars/page)
    │
    ▼
RecursiveCharacterTextSplitter
(800 tokens, overlap 150)
    │
    ▼
OpenAI text-embedding-3-small (1536 dims) → pgvector
    │
    ▼
RAG — 3 requêtes sémantiques parallèles
    │
    ▼
Claude Sonnet 4.6 (Anthropic) → JSON structuré validé Pydantic
    │
    ├── Résumé exécutif (scope, budget, risques, actions 48h)
    ├── Checklist (exigences, criticité, citations, confidence)
    └── Critères d'attribution (éligibilité + pondération notation)
```

---

## Flux utilisateur

1. S'inscrire / Se connecter
2. Créer un projet AO (titre, acheteur, date limite)
3. Uploader les PDFs du DCE (RC, CCTP, CCAP, DPGF…)
4. Lancer l'analyse IA (async ~2-5 min pour 200 pages)
5. Consulter : **Résumé** | **Checklist** | **Critères**
6. Exporter en **PDF**

---

## Types de documents reconnus

`RC` · `CCTP` · `CCAP` · `DPGF` · `BPU` · `AE` · `ATTRI` · `AUTRES`

---

## Lancer les tests

```bash
cd apps/api
pytest tests/ -v --tb=short

# Avec rapport de couverture
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Moteur IA

**Claude Sonnet 4.6** (Anthropic) est le moteur principal pour toutes les analyses :
- Context window 200K tokens → traite des DCE complets sans troncature
- Excellent sur les documents juridiques français (CCAP, RC, AE)
- JSON structuré fiable avec validation Pydantic

Les **embeddings** utilisent OpenAI `text-embedding-3-small` (meilleur rapport qualité/prix pour les vecteurs 1536D).

---

## Sécurité

- JWT HS256 (15min) + refresh token httpOnly cookie (7j, rotation)
- Isolation multi-tenant via `org_id` sur toutes les tables (Row-Level Security)
- URLs S3 toujours signées 15min, jamais directes
- Hashage IP SHA-256 pour access logs (conformité RGPD)
- `.env` dans `.gitignore` — ne jamais committer les clés

---

## Déploiement production (Scaleway Paris)

1. Build images Docker → registry Scaleway
2. Scaleway Managed Database pour PostgreSQL + pgvector
3. Scaleway Managed Redis
4. Scaleway Object Storage (Paris PAR1) pour les PDFs
5. Frontend → Vercel ou Scaleway Edge Services

> **Impératif RGPD** : hébergement exclusivement en Europe (Scaleway Paris PAR1).
