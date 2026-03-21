# AOPILOT — Value Improvement Plan (VIP)

**Date :** 21 mars 2026
**Objectif :** Passer de 25-45K€ (asset) à 200-400K€ (valorisation) en 12 mois

---

## 1. Situation Actuelle vs Cible

| Métrique | Aujourd'hui | Cible M+6 | Cible M+12 |
|----------|------------|-----------|------------|
| MRR | 0 € | 3 000 € | 8 000 € |
| Clients payants | 0 | 25 | 70 |
| Churn mensuel | N/A | < 8% | < 5% |
| NPS | N/A | > 30 | > 40 |
| Valorisation estimée | 25-45K€ | 90-150K€ | 200-400K€ |
| Structure juridique | EI | SASU | SAS (si associé) |

---

## 2. Axes d'Amélioration de Valeur

### Axe 1 — Validation Marché (Impact Valorisation : +300%)

**Pourquoi :** La différence entre 45K€ et 200K€ est entièrement la preuve de PMF. Un produit avec 25 clients payants et un churn < 8% vaut 5x plus qu'un MVP sans client.

| Action | Détail | Effort | Impact |
|--------|--------|--------|--------|
| Programme beta 10 entreprises BTP | Gratuit 3 mois, feedback structuré | 2 semaines | Critique |
| Onboarding white-glove | Accompagner chaque beta personnellement | Continu | Haut |
| Cas d'usage documentés | 3 success stories avec métriques (temps gagné, AO gagnés) | 1 semaine/cas | Très haut |
| ROI calculator | "X heures gagnées × Y AO/mois = Z€ économisés" | 2 jours | Haut |
| Webinaire mensuel | Démo live + Q&A avec prospects BTP | 0.5 jour/mois | Moyen |

### Axe 2 — Revenus Récurrents (Impact Valorisation : +200%)

| Action | Détail | Effort | Impact |
|--------|--------|--------|--------|
| Conversion beta → payant | Offre de lancement -50% sur 6 mois | 1 jour | Critique |
| Limiter plan Free | Passer de 5 à 2 docs/mois gratuits | 0.5 jour | Haut |
| Upsell automatique | Notifications in-app quand limite atteinte | 2 jours | Moyen |
| Facturation annuelle | Push -20% annuel dès l'inscription | 1 jour | Moyen |
| Pay-per-doc pour grands comptes | Offre sur mesure > 100 docs/mois | 1 jour | Moyen |

### Axe 3 — Produit Différenciant (Impact Valorisation : +100%)

| Action | Détail | Effort | Impact |
|--------|--------|--------|--------|
| Mémoire technique IA améliorée | Contenu narratif LLM par section (Phase 1A du plan) | 2 jours | Très haut |
| Graphiques dans exports | Radar Go/No-Go, courbe trésorerie (Phase 3) | 5 jours | Haut |
| Template DOCX professionnel | docxtpl avec design corporate (Phase 2) | 3 jours | Haut |
| Comparaison multi-AO | Tableau comparatif de plusieurs AO en pipeline | 5 jours | Moyen |
| Alertes intelligentes | Notification quand un AO match le profil entreprise | 3 jours | Haut |
| API publique documentée | Swagger/OpenAPI complet pour intégrations | 3 jours | Moyen |

### Axe 4 — Réduction des Risques (Impact Valorisation : +50%)

| Action | Détail | Effort | Impact |
|--------|--------|--------|--------|
| Transformation EI → SASU | Prérequis pour tout investissement | 500€ + 2 sem | Bloquant |
| Refonte site web | Aligner avec le produit réel, ajouter social proof | 5 jours | Haut |
| Tests frontend | Passer de 60 à 200+ tests | 5-8 jours | Moyen |
| Environnement staging | Réduire risque de déploiement | 2 jours | Moyen |
| Fallback multi-LLM | GPT-4o comme backup de Claude | 5 jours | Moyen |
| Migration embeddings EU | Mistral Embed pour conformité RGPD | 3 jours | Moyen |

---

## 3. Roadmap d'Exécution (12 mois)

### Phase 1 — Fondations (Mois 1-2) : "Préparer le lancement"

| Semaine | Actions |
|---------|---------|
| S1-S2 | Transformation EI → SASU + refonte site web |
| S3-S4 | Programme beta : recruter 10 entreprises BTP (LinkedIn, réseau) |
| S5-S6 | Onboarding beta + collecte feedback |
| S7-S8 | Itérations produit sur feedback + limiter plan Free |

**Deliverables :** SASU créée, site web cohérent, 10 betas actifs, premiers NPS

### Phase 2 — Traction (Mois 3-5) : "Prouver le PMF"

| Semaine | Actions |
|---------|---------|
| S9-S12 | Conversion betas → payants (offre lancement) |
| S13-S16 | 3 cas d'usage documentés (success stories) |
| S17-S20 | Amélioration mémoire technique IA + graphiques exports |
| Continu | Webinaires mensuels, contenu LinkedIn |

**Deliverables :** 15+ clients payants, 2K€+ MRR, 3 success stories, NPS > 30

### Phase 3 — Croissance (Mois 6-9) : "Accélérer"

| Mois | Actions |
|------|---------|
| M6 | SEO (blog BTP, guides AO), landing pages par segment |
| M7 | Partenariats fédérations BTP (FFB, CAPEB) |
| M8 | Template DOCX professionnel + alertes intelligentes |
| M9 | Tests frontend + staging + fallback multi-LLM |

**Deliverables :** 40+ clients, 5K€+ MRR, churn < 6%, 2 partenariats

### Phase 4 — Scale (Mois 10-12) : "Structurer"

| Mois | Actions |
|------|---------|
| M10 | API publique + documentation + webhooks avancés |
| M11 | Comparaison multi-AO + analytics avancés |
| M12 | Recruter 1er salarié (commercial ou dev) |

**Deliverables :** 70+ clients, 8K€+ MRR, prêt pour un seed round

---

## 4. Budget Estimé (12 mois)

| Poste | Coût estimé | Notes |
|-------|------------|-------|
| Transformation SASU | 500 — 1 000 € | Greffe + expert-comptable |
| Hébergement (Scaleway + Hostinger) | 1 200 — 2 400 € | ~100-200€/mois |
| API Claude (Anthropic) | 2 400 — 6 000 € | ~200-500€/mois selon volume |
| API OpenAI (embeddings) | 300 — 600 € | ~25-50€/mois |
| Domaine + email pro | 100 — 200 € | aopilot.fr |
| Marketing (LinkedIn Ads, salons) | 2 000 — 5 000 € | Budget minimal |
| Outils (Sentry, Stripe, etc.) | 600 — 1 200 € | ~50-100€/mois |
| **Total sans salarié** | **7 100 — 16 400 €** | — |
| Salarié (M10-M12, partiel) | 9 000 — 15 000 € | 3 mois × 3-5K€ |
| **Total avec salarié** | **16 100 — 31 400 €** | — |

### ROI Projeté

| Scénario | MRR M12 | ARR M12 | Coûts Y1 | Valorisation M12 | ROI |
|----------|---------|---------|----------|-------------------|-----|
| Pessimiste | 3 000 € | 36 000 € | 15 000 € | 90 000 € | 6x |
| Base | 8 000 € | 96 000 € | 20 000 € | 250 000 € | 12.5x |
| Optimiste | 15 000 € | 180 000 € | 25 000 € | 500 000 € | 20x |

---

## 5. KPIs de Suivi

### Tableau de Bord Mensuel

| KPI | M1 | M3 | M6 | M9 | M12 |
|-----|-----|-----|-----|-----|------|
| Signups (cumul) | 20 | 80 | 200 | 350 | 500 |
| Clients payants | 0 | 10 | 25 | 45 | 70 |
| MRR | 0€ | 1K€ | 3K€ | 5K€ | 8K€ |
| Churn mensuel | — | 10% | 7% | 5% | 4% |
| NPS | — | 25 | 35 | 40 | 45 |
| Coût LLM/revenue | — | 40% | 25% | 18% | 15% |
| AO analysés/mois | 10 | 50 | 150 | 300 | 500 |

### Milestones de Valorisation

| Milestone | Valorisation | Trigger |
|-----------|-------------|---------|
| MVP fonctionnel (actuel) | 25-45K€ | Code + architecture |
| Premiers 10 clients payants | 80-120K€ | PMF signal |
| 3K€ MRR + churn < 8% | 100-150K€ | PMF validé |
| 8K€ MRR + croissance > 10% MoM | 250-400K€ | Growth phase |
| 20K€ MRR + NRR > 100% | 600K-1M€ | Scale ready |

---

## 6. Quick Wins Immédiats (Semaine 1)

| Action | Effort | Impact attendu |
|--------|--------|---------------|
| Publier 3 posts LinkedIn sur l'analyse DCE par IA | 2h | Visibilité + leads |
| Créer une landing page "/demo" avec Calendly | 1h | Conversion visitors → démos |
| Envoyer 20 emails ciblés à des PME BTP (réseau personnel) | 3h | 2-5 betas potentiels |
| Corriger les incohérences du site (pricing, stack, logos) | 4h | Crédibilité |
| Limiter le plan Free à 2 docs/mois dans le code | 30min | Réduire coûts, pousser conversion |

---

*Ce plan est conçu pour un solo founder bootstrappé. Les timelines s'accélèrent significativement avec un co-fondateur ou un investissement seed de 50-100K€.*
