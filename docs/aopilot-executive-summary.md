# AOPILOT — Executive Summary Due Diligence

**Date :** 21 mars 2026
**Statut :** Pre-revenue / MVP fonctionnel
**Entité :** Entreprise Individuelle (EI)
**Domaine :** aopilot.fr

---

## Score Global : 4.8 / 10

| Dimension | Score | Commentaire |
|-----------|-------|-------------|
| Produit & Technologie | 7.5/10 | Stack moderne, 48K LOC, 116+ endpoints, 18 analyses IA |
| Market Fit | 5.0/10 | Niche BTP pertinente mais non validée par le marché |
| Traction & Revenus | 1.0/10 | Pre-revenue, aucun client payant, pas de MRR |
| Équipe | 3.0/10 | Solo founder (EI), pas de co-fondateur technique/commercial |
| Go-to-Market | 2.5/10 | Site web incohérent avec le produit, 0 social proof |
| Scalabilité | 6.0/10 | Architecture multi-tenant RLS, Celery workers, prêt à scaler |
| Propriété Intellectuelle | 5.0/10 | Code propriétaire mais pas de brevet, dépendance Claude API |
| Risques réglementaires | 7.0/10 | RGPD implémenté, hébergement EU (Scaleway Paris) |

---

## Résumé Exécutif

AOPILOT est un micro-SaaS B2B d'analyse automatique de Dossiers de Consultation des Entreprises (DCE) pour le secteur BTP français. Le produit utilise l'IA (Claude Sonnet d'Anthropic) pour extraire, analyser et scorer les appels d'offres publics, générant des rapports Go/No-Go, des mémoires techniques et des simulations de trésorerie.

### Points Forts
- **Produit techniquement abouti** : 48K LOC, 18 modules d'analyse IA, export PDF/DOCX/Mémo, pipeline complet upload → analyse → scoring → export
- **Niche défendable** : Marché BTP français (70-90 Mds€/an d'AO), barrière linguistique et réglementaire forte
- **Architecture scalable** : Multi-tenant PostgreSQL RLS, Celery workers async, pgvector pour RAG
- **Couverture test** : 66% backend (820 tests), CI/CD GitHub Actions fonctionnel

### Points Faibles Critiques
- **Zero revenue, zero client** : Aucune validation marché, pas de PMF démontré
- **Solo founder en EI** : Risque homme-clé maximal, structure juridique inadaptée à la levée
- **Incohérences site/produit** : Site mentionne Mistral/Jina alors que le code utilise Claude/OpenAI ; pricing différent
- **Coût d'acquisition non testé** : Aucun canal d'acquisition validé, CAC inconnu

### Valorisation Estimée

| Scénario | Valorisation | Méthode |
|----------|-------------|---------|
| Asset sale (pre-revenue) | 15 000 — 50 000 € | Coût de remplacement pondéré |
| Avec 5K€ MRR validé | 150 000 — 300 000 € | 2.5-5x ARR |
| Avec 20K€ MRR + croissance | 600 000 — 1 200 000 € | 2.5-5x ARR + prime croissance |
| Bull case (50K€ MRR, leader niche) | 2 000 000 — 4 000 000 € | 3-5x ARR |

### Recommandation

**Investissement :** Non recommandé en l'état. L'actif a une valeur technologique réelle (15-50K€ en remplacement de dev) mais aucune preuve de marché.

**Conditions pour reconsidérer :**
1. Transformation en SAS (ou SASU minimum)
2. Acquisition de 10+ clients payants (validation PMF)
3. Atteinte de 3K€+ MRR avec rétention > 85%
4. Recrutement d'un co-fondateur commercial ou technique

---

*Rapport complet dans les fichiers associés : technical-dd, market-benchmark, risk-register, valuation-report, value-improvement-plan.*
