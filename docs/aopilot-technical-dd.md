# AOPILOT — Due Diligence Technique

**Date :** 21 mars 2026
**Score technique global : 7.5 / 10**

---

## 1. Architecture Overview

### 1.1 Stack Technologique

| Couche | Technologie | Version | Maturité |
|--------|------------|---------|----------|
| Frontend | Next.js (App Router) | 14 | Stable, mainstream |
| UI | React + TypeScript + Tailwind + shadcn/ui | — | Standard industriel |
| State | Zustand + React Query | — | Léger, performant |
| Backend | FastAPI + Python | 3.12 | Production-ready |
| ORM | SQLAlchemy | 2.x | Standard Python |
| DB | PostgreSQL + pgvector | 16 | Enterprise-grade |
| Queue | Celery + Redis | — | Éprouvé, scalable |
| IA | Anthropic Claude Sonnet 4.6 | — | Top-tier LLM |
| Embeddings | OpenAI text-embedding-3-small | — | Standard |
| Storage | Scaleway S3-compatible | — | EU souverain |
| CI/CD | GitHub Actions | — | Standard |

### 1.2 Métriques Codebase

| Métrique | Valeur | Évaluation |
|----------|--------|-----------|
| LOC total | ~48 000 | Conséquent pour un solo dev |
| Fichiers backend | ~80+ | Bien structuré en modules |
| Fichiers frontend | ~60+ | Organisation par feature |
| Endpoints API | 116+ | Couverture fonctionnelle large |
| Modèles DB | 16 | Schéma normalisé |
| Migrations Alembic | 18 | Historique propre |
| Tests backend | 820 (48 fichiers) | Bon volume |
| Tests frontend | 60 (6 fichiers) | Insuffisant |
| Couverture backend | 66% | Correcte, cible 80%+ |
| Couverture frontend | Non mesurée | Risque |

---

## 2. Analyse Module par Module

### 2.1 Modules d'Analyse IA (18 analyseurs)

| Module | LOC | Tests | Couverture | Qualité |
|--------|-----|-------|-----------|---------|
| analyzer.py (orchestrateur) | ~400 | Oui | 79% | Bonne |
| ccap_analyzer.py | ~350 | Oui | 96% | Excellente |
| rc_analyzer.py | ~300 | Oui | 100% | Excellente |
| ae_analyzer.py | ~250 | Oui | 100% | Excellente |
| cctp_analyzer.py | ~300 | Oui | 98% | Excellente |
| subcontracting_analyzer.py | ~200 | Oui | 100% | Excellente |
| cashflow_simulator.py | ~350 | Oui | 85% | Bonne |
| scoring_simulator.py | ~300 | Oui | 90% | Bonne |
| prompts.py | ~511 | Non | 0% | Risque (non testé) |
| llm.py | ~200 | Partiel | 20% | À améliorer |

### 2.2 Module Export (refactoré)

| Fichier | LOC | Rôle | État |
|---------|-----|------|------|
| exporter.py | 405 | Orchestration PDF | Refactoré ✓ |
| export_data.py | 277 | Fetch centralisé | Refactoré ✓ |
| docx_exporter.py | 1783 | Export Word | Corrigé récemment |
| memo_exporter.py | 1174 | Mémoire technique | Corrigé récemment |
| template.html | 1729 | Template PDF Jinja2 | Thémable |
| report_theme.py | ~50 | Configuration couleurs | Nouveau |
| chart_generator.py | ~200 | Graphiques matplotlib | Nouveau, testé |

### 2.3 Modules Infrastructure

| Module | LOC | Qualité | Notes |
|--------|-----|---------|-------|
| billing.py (Stripe) | ~300 | Correcte | 6 plans, webhooks Stripe |
| gdpr.py | ~200 | Bonne | Export/purge conformes |
| webhook_dispatch.py | ~270 | Bonne | Fan-out + retry backoff |
| storage.py | ~150 | Excellente | 97% coverage, S3 sécurisé |
| embedder.py | ~200 | Correcte | pgvector 1536 dims |
| retriever.py | ~250 | Correcte | RAG cosine similarity |

---

## 3. Sécurité

### 3.1 Audit Sécurité

| Contrôle | Statut | Détails |
|----------|--------|---------|
| Authentification JWT | ✅ Implémenté | HS256, 15min access + 7j refresh rotation |
| Multi-tenant RLS | ✅ Implémenté | org_id sur toutes les tables |
| CORS strict | ✅ Corrigé | Origins whitelistés |
| Rate limiting | ✅ Implémenté | Par IP et par user |
| SSRF protection | ✅ Corrigé | Validation URLs |
| CSP headers | ✅ Implémenté | Content-Security-Policy |
| Signed URLs S3 | ✅ Implémenté | 15min expiration |
| RGPD | ✅ Implémenté | Export + purge auto |
| SSO SAML | ✅ Implémenté | Plan Business |
| API Keys scoped | ✅ Implémenté | 6 scopes granulaires |

### 3.2 Vulnérabilités Identifiées

| Risque | Sévérité | Statut |
|--------|----------|--------|
| JWT HS256 (devrait être RS256 en prod multi-service) | Moyen | À migrer |
| Secrets dans variables d'environnement (pas de vault) | Moyen | Acceptable en early-stage |
| Pas d'audit de dépendances automatisé (Dependabot) | Faible | À activer |
| Tests de sécurité automatisés absents (SAST/DAST) | Moyen | À implémenter |

---

## 4. Dette Technique

### 4.1 Dette Identifiée

| Zone | Sévérité | Impact | Effort de correction |
|------|----------|--------|---------------------|
| Frontend peu testé (60 tests, 6 fichiers) | Haute | Régressions silencieuses | 5-8 jours |
| `llm.py` couverture 20% | Haute | Pas de filet sur le coeur IA | 3-5 jours |
| `prompts.py` non testé | Moyenne | Dérive des outputs LLM | 2-3 jours |
| Pas de monitoring APM | Moyenne | Blind spots performance | 2-3 jours |
| Pas de load testing | Moyenne | Capacité inconnue | 2-3 jours |
| Hardcoded config dans certains services | Faible | Difficile à reconfigurer | 1-2 jours |
| **Total dette technique** | — | — | **15-24 jours** |

### 4.2 Qualité du Code

| Critère | Score | Détails |
|---------|-------|---------|
| Lisibilité | 8/10 | Noms clairs, structlog, docstrings |
| Modularité | 7/10 | Bien découpé post-refactoring (sprint Audit 3) |
| Cohérence | 6/10 | Quelques inconsistances de nommage (FR/EN mix) |
| Maintenabilité | 7/10 | Bonne structure, mais solo dev = bus factor 1 |
| Performance | 6/10 | Pas de profiling, requêtes N+1 possibles |

---

## 5. Infrastructure & DevOps

### 5.1 Pipeline CI/CD

```
GitHub Actions:
  test-backend (pytest) → test-frontend (vitest) → push-images (ghcr.io) → deploy-backend (SSH Scaleway) → deploy-frontend (Hostinger API)
```

| Aspect | Statut | Notes |
|--------|--------|-------|
| CI automatisé | ✅ | Tests backend + frontend |
| CD automatisé | ✅ | Deploy via SSH + Hostinger API |
| Environnement staging | ❌ | Pas de staging, direct en prod |
| Infrastructure as Code | ❌ | Pas de Terraform/Pulumi |
| Monitoring | Partiel | Sentry + structlog, pas de Grafana actif |
| Backups | ✅ | pg_dump → S3, rétention 30j |
| Purge RGPD | ✅ | Celery beat automatique |

### 5.2 Scalabilité

| Composant | Capacité estimée | Bottleneck |
|-----------|-----------------|------------|
| API FastAPI | ~500 req/s | CPU-bound (LLM calls) |
| Celery workers | Horizontal scaling | Redis broker |
| PostgreSQL | ~100K projets | Pas de read replicas |
| S3 Storage | Illimité | Coût proportionnel |
| LLM (Claude API) | Rate-limited par Anthropic | Coût variable (~0.02€/analyse) |

---

## 6. Estimation Productionisation

| Tâche | Effort | Priorité |
|-------|--------|----------|
| Audit sécurité externe | 3-5 jours | Critique |
| Environnement staging | 2-3 jours | Haute |
| Monitoring APM (Grafana/Datadog) | 2-3 jours | Haute |
| Load testing | 2-3 jours | Haute |
| Tests frontend (coverage > 50%) | 5-8 jours | Haute |
| Migration JWT RS256 | 1-2 jours | Moyenne |
| IaC (Terraform) | 3-5 jours | Moyenne |
| Documentation API (OpenAPI complète) | 2-3 jours | Moyenne |
| **Total** | **20-32 jours** | — |

---

## 7. Verdict Technique

### Forces
- Architecture moderne et bien structurée pour un projet solo
- 18 modules d'analyse IA couvrant le workflow BTP complet
- Multi-tenant RLS natif = prêt pour le SaaS
- Refactoring récent du module export (de 5044L monolithique à 4 modules)
- 820 tests backend avec 66% de couverture

### Faiblesses
- Bus factor = 1 (solo developer)
- Frontend sous-testé
- Pas de staging ni de load testing
- Mix FR/EN dans le code et les nommages
- Dépendance forte à l'API Claude (pas de fallback LLM)

### Recommandation
Le code est de qualité correcte pour un MVP. 10-15 semaines de travail supplémentaires sont nécessaires pour atteindre un niveau production-grade. L'architecture est saine et permet une montée en charge progressive.
