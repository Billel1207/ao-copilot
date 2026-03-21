# AOPILOT — Risk Register

**Date :** 21 mars 2026
**Niveau de risque global : ÉLEVÉ (7.2 / 10)**

---

## 1. Matrice de Risques

| ID | Catégorie | Risque | Probabilité | Impact | Score | Mitigation |
|----|-----------|--------|-------------|--------|-------|------------|
| R01 | Business | Aucune traction marché (0 client payant) | 100% | Critique | **10** | Lancer programme early adopters immédiat |
| R02 | Équipe | Solo founder, bus factor = 1 | 100% | Critique | **10** | Recruter co-fondateur ou CTO |
| R03 | Juridique | Entité EI inadaptée (pas de levée possible) | 100% | Haute | **8** | Transformer en SAS/SASU |
| R04 | Tech | Dépendance Claude API (Anthropic) — pricing, disponibilité | 60% | Haute | **7.2** | Implémenter fallback multi-LLM |
| R05 | Business | Site web incohérent avec le produit réel | 100% | Moyenne | **7** | Refonte complète du site |
| R06 | Marché | Cycle de vente BTP long (3-6 mois) | 80% | Haute | **7.2** | Offre trial gratuite + ROI calculator |
| R07 | Tech | Frontend sous-testé (60 tests / 6 fichiers) | 80% | Moyenne | **6.4** | Sprint tests frontend (5-8j) |
| R08 | Concurrence | Vecteur Plus ajoute l'IA à ses 6000 clients | 40% | Critique | **6** | Accélérer la mise en marché |
| R09 | Réglementaire | Évolution Code des marchés publics | 30% | Haute | **4.5** | Veille juridique, prompts adaptables |
| R10 | Finance | Coûts LLM > revenus (plan Free = perte nette) | 70% | Moyenne | **5.6** | Limiter plan Free à 3 docs, optimiser prompts |
| R11 | Tech | Pas d'environnement staging | 70% | Moyenne | **5.6** | Déployer staging sur Scaleway |
| R12 | Sécurité | JWT HS256 en production | 30% | Haute | **4.5** | Migrer vers RS256 |
| R13 | RGPD | Transfert données hors EU (OpenAI embeddings) | 50% | Haute | **5** | Migrer vers embeddings EU (Mistral) |
| R14 | Marché | Adoption IA lente dans le BTP traditionnel | 60% | Moyenne | **4.8** | Focus PME tech-forward, preuves ROI |
| R15 | Tech | Scalabilité non testée (pas de load test) | 50% | Moyenne | **4** | Implémenter load testing |

---

## 2. Risques par Catégorie

### 2.1 Risques Business (Critiques)

#### R01 — Aucune Traction Marché
- **Statut :** ACTIF — Risque maximal
- **Description :** Le produit est fonctionnel depuis mars 2026 mais aucun client payant n'a été acquis. Aucune preuve de Product-Market Fit.
- **Conséquence :** Valorisation plancher (asset only), impossible de lever des fonds
- **Mitigation :**
  1. Lancer un programme de 10 beta testers BTP (gratuit, 3 mois)
  2. Collecter des métriques d'usage et NPS
  3. Itérer le produit sur le feedback réel
  4. Convertir 3+ betas en payants
- **KPI de suivi :** Nombre de signups, activation rate, NPS

#### R06 — Cycle de Vente Long
- **Statut :** ACTIF
- **Description :** Les entreprises BTP ont des processus de décision lents. Un outil SaaS IA est perçu comme risqué par les dirigeants BTP traditionnels.
- **Mitigation :**
  1. Offrir une démo gratuite sur un vrai DCE du prospect
  2. Créer un ROI calculator ("temps gagné par AO × nombre d'AO/an")
  3. Cibler les "innovation managers" des ETI BTP
  4. Proposer un POC gratuit de 30 jours

### 2.2 Risques Techniques

#### R04 — Dépendance Claude API
- **Statut :** ACTIF
- **Description :** 100% des analyses IA passent par l'API Claude Sonnet d'Anthropic. Un changement de pricing (hausse de 50%+), une interruption de service, ou un changement de politique pourrait paralyser le produit.
- **Conséquence :** Marge brute imprévisible, risque opérationnel
- **Mitigation :**
  1. Implémenter une couche d'abstraction LLM (déjà `llm.py`)
  2. Tester les prompts avec GPT-4o et Mistral Large comme fallbacks
  3. Mettre en cache les résultats d'analyse (déjà fait via `ExtractionResult`)
  4. Négocier un volume discount avec Anthropic
- **Coût de mitigation :** 5-8 jours de développement

#### R07 — Frontend Sous-Testé
- **Statut :** ACTIF
- **Description :** 60 tests sur 6 fichiers seulement. Les 18 onglets d'analyse, les formulaires de paramétrage, et le workflow d'upload ne sont pas testés.
- **Conséquence :** Régressions silencieuses sur l'UX, bugs non détectés
- **Mitigation :** Sprint dédié de 5-8 jours, cibler les composants critiques (upload, export, billing)

#### R13 — Transfert Données Hors EU (OpenAI Embeddings)
- **Statut :** ACTIF
- **Description :** Les embeddings passent par l'API OpenAI (serveurs US). Pour des documents de marchés publics français, cela pose un risque RGPD (transfert hors EU).
- **Mitigation :**
  1. Migrer vers Mistral Embed (hébergé en France)
  2. Ou utiliser un modèle local (e5-large, all-MiniLM)
  3. Documenter la base légale du transfert (clauses contractuelles types)

### 2.3 Risques Juridiques

#### R03 — Structure EI Inadaptée
- **Statut :** ACTIF — Bloquant pour levée de fonds
- **Description :** L'Entreprise Individuelle ne permet pas d'émettre des actions, d'accueillir des investisseurs, ni de structurer un BSPCE. La responsabilité est personnelle et illimitée.
- **Conséquence :** Impossible de lever des fonds, pas de séparation patrimoine personnel/professionnel
- **Mitigation :**
  1. Transformer en SASU (coût ~500-1000€, 2-4 semaines)
  2. Ou créer une SAS ab initio et faire un apport en nature du code
  3. Valorisation de l'apport par commissaire aux apports si > 30K€

### 2.4 Risques Concurrentiels

#### R08 — Vecteur Plus Ajoute l'IA
- **Statut :** LATENT
- **Description :** Vecteur Plus (6000 clients, leader veille AO France) pourrait développer des fonctionnalités d'analyse IA similaires à AOPILOT. Avec leur base client existante, l'adoption serait immédiate.
- **Probabilité :** 40% sur 18 mois (IA trending, ils ont les moyens)
- **Mitigation :**
  1. Lancer le produit rapidement pour construire une base d'utilisateurs
  2. Se différencier par la profondeur d'analyse (18 modules vs feature simple)
  3. Construire des moats (données d'usage, références, intégrations)
  4. Envisager un partenariat ou une acquisition par Vecteur Plus

---

## 3. Heatmap des Risques

```
Impact ↑
         │
Critique │  R01  R02          R08
         │
   Haute │  R03  R04  R06     R09  R13
         │
 Moyenne │  R05  R07  R10  R11     R14  R15
         │
  Faible │                    R12
         │
         └──────────────────────────────────→
           Faible  Moyenne   Haute  Critique
                                    Probabilité
```

---

## 4. Plan d'Action Prioritisé

| Priorité | Action | Risques adressés | Effort | Deadline |
|----------|--------|-----------------|--------|----------|
| 🔴 P0 | Programme 10 beta testers BTP | R01, R06, R14 | 2 semaines | Avril 2026 |
| 🔴 P0 | Transformation EI → SASU/SAS | R03 | 500-1000€ + 2 sem | Avril 2026 |
| 🟠 P1 | Refonte site web (cohérence produit) | R05 | 5 jours | Mai 2026 |
| 🟠 P1 | Limiter plan Free (3 docs) + analytics | R10 | 1 jour | Avril 2026 |
| 🟡 P2 | Tests frontend sprint | R07 | 5-8 jours | Juin 2026 |
| 🟡 P2 | Environnement staging | R11 | 2-3 jours | Mai 2026 |
| 🟡 P2 | Abstraction multi-LLM (fallback GPT-4o) | R04 | 5-8 jours | Juillet 2026 |
| 🟢 P3 | Migration embeddings EU (Mistral) | R13 | 3-5 jours | Q3 2026 |
| 🟢 P3 | JWT RS256 | R12 | 1-2 jours | Q3 2026 |
| 🟢 P3 | Load testing | R15 | 2-3 jours | Q3 2026 |

---

## 5. Indicateurs de Suivi

| Indicateur | Fréquence | Seuil d'alerte |
|-----------|-----------|----------------|
| Nombre de clients payants | Hebdo | < 5 à M+3 |
| MRR | Mensuel | < 1K€ à M+6 |
| Churn rate | Mensuel | > 10% |
| Coût LLM / revenu | Mensuel | > 30% |
| Uptime API Claude | Quotidien | < 99% |
| NPS beta testers | Mensuel | < 20 |
| Temps moyen analyse DCE | Hebdo | > 10 minutes |
