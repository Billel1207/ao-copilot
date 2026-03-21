# AOPILOT — Rapport de Valorisation

**Date :** 21 mars 2026
**Analyste :** Due Diligence Automatisée
**Version :** 1.0

---

## 1. Méthode de Valorisation

Trois approches combinées pour un actif pre-revenue :

| Méthode | Applicable ? | Justification |
|---------|-------------|---------------|
| DCF (Discounted Cash Flow) | Partiellement | Pas de revenus historiques → projections spéculatives |
| Multiples de marché (ARR) | Conditionnelle | Applicable si MRR > 0, multiples SaaS B2B niche |
| Coût de remplacement | Oui | Méthode principale pour un actif pre-revenue |

---

## 2. Valorisation par Coût de Remplacement

### 2.1 Estimation du Coût de Développement

| Composant | LOC estimées | Jours-homme | Coût (500€/j) |
|-----------|-------------|-------------|---------------|
| Backend FastAPI (API + Services) | ~25 000 | 80-100 | 40 000 — 50 000 € |
| Frontend Next.js 14 | ~15 000 | 50-65 | 25 000 — 32 500 € |
| Analyses IA (18 modules + prompts) | ~5 000 | 30-40 | 15 000 — 20 000 € |
| Infrastructure (CI/CD, Docker, migrations) | ~3 000 | 15-20 | 7 500 — 10 000 € |
| Tests (820 backend + 60 frontend) | — | 20-25 | 10 000 — 12 500 € |
| **Total brut** | **~48 000** | **195-250** | **97 500 — 125 000 €** |

### 2.2 Facteurs de Décote

| Facteur | Décote | Raison |
|---------|--------|--------|
| Code non audité en production | -30% | Bugs non découverts, dette technique cachée |
| Solo developer, pas de documentation exhaustive | -15% | Risque de reprise difficile |
| Dépendance API externe (Claude Sonnet) | -10% | Pas de moat technique propre |
| Pre-revenue (pas de PMF validé) | -20% | Le code résout peut-être le mauvais problème |
| Stack moderne et maintenable | +10% | FastAPI + Next.js 14 = recrutement facile |
| Tests existants (66% coverage) | +5% | Réduit le risque de régression |

**Décote nette : -60%**

### 2.3 Valorisation Asset

| Scénario | Calcul | Valorisation |
|----------|--------|-------------|
| Pessimiste | 97 500 × 0.15 | **14 625 €** |
| Base | 110 000 × 0.40 | **44 000 €** |
| Optimiste | 125 000 × 0.50 | **62 500 €** |

**Fourchette retenue : 15 000 — 50 000 €**

---

## 3. Valorisation par Multiples (Scénarios avec Revenue)

### 3.1 Multiples de Référence SaaS B2B Niche (2025-2026)

| Segment | Multiple ARR médian | Source |
|---------|-------------------|--------|
| SaaS B2B early-stage (< 1M€ ARR) | 2-4x | MicroAcquire/Acquire.com |
| SaaS B2B niche verticale | 3-6x | SaaS Capital Index |
| GovTech / RegTech SaaS | 4-8x | PitchBook GovTech |
| Micro-SaaS bootstrappé | 2-3.5x | Quiet Light, FE International |

### 3.2 Scénarios de Valorisation

| Scénario | MRR | ARR | Multiple | Valorisation |
|----------|-----|-----|----------|-------------|
| Seed (validation initiale) | 3 000 € | 36 000 € | 3x | 108 000 € |
| Traction (PMF atteint) | 5 000 € | 60 000 € | 3.5x | 210 000 € |
| Growth (croissance prouvée) | 15 000 € | 180 000 € | 4x | 720 000 € |
| Scale (leader niche FR) | 50 000 € | 600 000 € | 5x | 3 000 000 € |

### 3.3 Ajustements Spécifiques

| Facteur | Impact sur multiple |
|---------|-------------------|
| Net Revenue Retention > 110% | +0.5-1x |
| Churn < 5% mensuel | +0.5x |
| Croissance MoM > 15% | +1-2x |
| Solo founder (key-man risk) | -1x |
| Pas de moat technique fort | -0.5x |
| Niche réglementaire (barrière entrée) | +0.5x |

---

## 4. Valorisation DCF (Projection 5 ans)

### 4.1 Hypothèses

| Paramètre | Valeur |
|-----------|--------|
| Taux d'actualisation | 35% (early-stage, risque élevé) |
| Croissance Year 1 | 0 → 5K€ MRR (acquisition 70 clients Starter) |
| Croissance Year 2 | 5K → 15K€ MRR (upsell Pro + nouveaux) |
| Croissance Year 3 | 15K → 35K€ MRR (Europe plan + Business) |
| Croissance Year 4-5 | 35K → 60K€ MRR (saturation niche) |
| Marge brute | 75% (coûts LLM ~ 15%, infra ~ 10%) |
| Terminal multiple | 3x ARR |

### 4.2 Projection Cash Flows

| Année | MRR fin | ARR | Marge brute | Cash flow net |
|-------|---------|-----|-------------|---------------|
| Y1 | 5 000 € | 60 000 € | 75% | -30 000 € (investissement) |
| Y2 | 15 000 € | 180 000 € | 75% | 50 000 € |
| Y3 | 35 000 € | 420 000 € | 78% | 180 000 € |
| Y4 | 50 000 € | 600 000 € | 80% | 300 000 € |
| Y5 | 60 000 € | 720 000 € | 80% | 380 000 € |

### 4.3 DCF Résultat

| Composant | Valeur |
|-----------|--------|
| PV des cash flows (Y1-Y5) | ~320 000 € |
| Terminal value (3x ARR Y5, actualisé) | ~490 000 € |
| **Valeur d'entreprise DCF** | **~810 000 €** |
| Probabilité d'exécution (pre-revenue) | 15-25% |
| **Valeur ajustée au risque** | **120 000 — 200 000 €** |

---

## 5. Synthèse Valorisation

| Méthode | Fourchette | Confiance |
|---------|-----------|-----------|
| Coût de remplacement | 15 000 — 50 000 € | Haute |
| Multiples ARR (si 5K MRR) | 150 000 — 300 000 € | Moyenne |
| DCF ajusté risque | 120 000 — 200 000 € | Faible |

### Valorisation Recommandée

**Aujourd'hui (pre-revenue) : 25 000 — 45 000 €**
- Plancher : valeur de liquidation du code
- Plafond : valeur pour un acquéreur stratégique (ex: éditeur BTP existant)

**Post-PMF (5K€ MRR, 6+ mois) : 150 000 — 250 000 €**

---

## 6. Comparables

| Entreprise | Segment | Stade | Valorisation connue |
|-----------|---------|-------|-------------------|
| Stotles (UK) | Procurement intelligence | Series A | ~$15M (2023) |
| Vecteur Plus (FR) | Veille AO | Établi, 6000 clients | Non publique, >10M€ |
| Spendbase | Procurement SaaS | Seed | ~$3M (2024) |
| Tender Alpha | Tender analytics | Pre-seed | ~$500K (2023) |

**AOPILOT se situe entre Tender Alpha (pre-seed) et un petit Spendbase, avec la spécificité BTP France.**

---

## 7. Conditions de Deal Recommandées

### Pour un Acquéreur
- Prix d'acquisition : 30 000 — 45 000 € (asset deal)
- Clause d'earn-out sur 12 mois : +20 000 € si 3K€ MRR atteint
- Période de transition : 3 mois minimum (transfert de connaissances)
- Due diligence technique : audit de sécurité externe obligatoire

### Pour un Investisseur (Pre-seed)
- Valorisation pre-money : 150 000 — 250 000 € (post transformation SAS)
- Ticket : 50 000 — 100 000 € pour 20-40% du capital
- Milestones : 10 clients payants en 6 mois, 5K€ MRR en 12 mois
- Gouvernance : board advisor, reporting mensuel
