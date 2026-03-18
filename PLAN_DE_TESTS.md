# PLAN DE TESTS EXHAUSTIF — AO Copilot

> Produit le 2026-03-17 par QA Engineer Senior
> Backend : 12 fichiers test existants (~85 tests), couverture ~35%
> Frontend : 3 fichiers test existants (~8 tests), couverture ~15%
> Cibles : Backend 70% | Frontend 50%

---

## ETAT DES LIEUX

### Tests backend existants (apps/api/tests/)
| Fichier | Lignes | Couverture |
|---------|--------|------------|
| test_auth.py | 68 | auth routes |
| test_projects.py | 95 | CRUD projets |
| test_documents.py | 296 | upload, extraction |
| test_analysis.py | 179 | trigger analyse |
| test_billing.py | 334 | Stripe, quotas |
| test_cashflow.py | 108 | simulate_cashflow |
| test_gonogo.py | 114 | compute_profile_match |
| test_validators.py | 145 | Pydantic validators |
| test_gdpr.py | 244 | delete, export, unsub |
| test_rls.py | 240 | isolation multi-tenant |
| test_integration_webhooks.py | 351 | webhook dispatch |
| conftest.py | 210 | fixtures |

### Services NON testés (19 fichiers)
ccap_analyzer, cctp_analyzer, rc_analyzer, ae_analyzer, conflict_detector,
subcontracting_analyzer, questions_generator, scoring_simulator, btp_pricing,
dc_checker, language_detect, retriever, llm, exporter, verification,
analyzer (orchestrateur), chunker, dpgf_extractor, analytics

### Tests frontend existants (apps/web/src/)
- LoginForm.test.tsx
- DropZone.test.tsx
- auth.test.ts (store)

---

## PARTIE 1 — TESTS UNITAIRES BACKEND (cible 70%)

---

### test_ccap_analyzer.py
**Fichier source** : `apps/api/app/services/ccap_analyzer.py`
**Fonction testee** : `analyze_ccap_risks(text, project_id=None)`
**Fixtures** : `mock_llm` (patch `llm_service.complete_json`)

```
Tests a implementer :

1. test_analyze_ccap_risks_nominal_returns_valid_structure
   - Setup : texte CCAP factice avec clause penalites + retenue
   - Mock LLM retourne : {"clauses_risquees": [...], "score_risque_global": 65, "resume": "...", "recommendations": [...], "confidence_overall": 0.85}
   - Expected : dict avec cles clauses_risquees, score_risque_global, resume, recommendations, confidence_overall
   - Assert : score_risque_global entre 0 et 100, confidence_overall entre 0.0 et 1.0

2. test_analyze_ccap_risks_empty_text_returns_empty_result
   - Input : text=""
   - Expected : resultat avec clauses_risquees=[] ou score=0
   - Mock : LLM ne doit PAS etre appele (guard clause)

3. test_analyze_ccap_risks_penalites_critiques_detected
   - Mock LLM retourne clause avec severity="CRITIQUE" pour penalites > 1/1000
   - Assert : au moins une clause avec criticality="CRITIQUE"

4. test_analyze_ccap_risks_retenue_garantie_above_5pct
   - Mock LLM retourne clause retenue garantie 10% flaggee "HAUT"
   - Assert : presence dans clauses_risquees

5. test_analyze_ccap_risks_ccag_context_injected
   - Verify : system_prompt contient references CCAG-Travaux 2021
   - Mock : capture le system_prompt passe a complete_json

6. test_analyze_ccap_risks_jurisprudence_context_injected
   - Verify : system_prompt contient contexte jurisprudence

7. test_analyze_ccap_risks_llm_failure_raises_or_returns_empty
   - Mock LLM raise Exception
   - Expected : gere gracieusement (empty result ou raise specifique)

8. test_analyze_ccap_risks_validated_pydantic_model
   - Mock LLM retourne donnees invalides (score=-5)
   - Expected : ValidatedCcapAnalysis normalise le score a 0
```

---

### test_cctp_analyzer.py
**Fichier source** : `apps/api/app/services/cctp_analyzer.py`
**Fonction testee** : `analyze_cctp(text, project_id=None)`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_analyze_cctp_nominal_returns_8_categories
   - Mock LLM retourne 8 categories techniques
   - Assert : structure valide, chaque categorie a name + items

2. test_analyze_cctp_empty_text_returns_empty
   - Input : text=""
   - Expected : _empty_result() retourne

3. test_analyze_cctp_materiaux_detected
   - Mock : categorie "materiaux" avec specifications beton, acier
   - Assert : au moins 1 item dans categorie materiaux

4. test_analyze_cctp_normes_techniques_detected
   - Mock : normes NF, DTU, Eurocode detectees
   - Assert : references normatives presentes

5. test_analyze_cctp_contradictions_intra_document
   - Mock : contradictions detectees dans le CCTP lui-meme
   - Assert : champ contradictions non vide

6. test_analyze_cctp_confidence_scoring
   - Mock retourne confidence=0.3
   - Assert : confidence < 0.5 flagge comme low confidence

7. test_analyze_cctp_pydantic_validation
   - Mock retourne donnees hors schema
   - Expected : ValidatedCctpAnalysis corrige

8. test_analyze_cctp_llm_timeout_handled
   - Mock LLM raise TimeoutError
   - Expected : erreur geree proprement
```

---

### test_rc_analyzer.py
**Fichier source** : `apps/api/app/services/rc_analyzer.py`
**Fonction testee** : `analyze_rc(text, project_id=None)`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_analyze_rc_nominal_structure
   - Mock retourne : conditions, lots, variantes, sous_traitance, dates
   - Assert : toutes les cles presentes

2. test_analyze_rc_empty_text
   - Input : ""
   - Expected : resultat vide ou guard clause

3. test_analyze_rc_lots_detected
   - Mock : 3 lots avec numeros et intitules
   - Assert : lots est liste de 3 items

4. test_analyze_rc_variantes_autorisees
   - Mock : variantes_autorisees=true
   - Assert : champ variantes correct

5. test_analyze_rc_groupement_conjoint
   - Mock : groupement type="conjoint" avec mandataire
   - Assert : groupement parse correctement

6. test_analyze_rc_dates_soumission
   - Mock : date_limite="2026-04-01"
   - Assert : date parsee et presente

7. test_analyze_rc_sous_traitance_conditions
   - Mock : restrictions sous-traitance
   - Assert : conditions de sous-traitance presentes

8. test_analyze_rc_pydantic_validation
   - Mock : donnees invalides
   - Expected : normalisation par validator
```

---

### test_ae_analyzer.py
**Fichier source** : `apps/api/app/services/ae_analyzer.py`
**Fonction testee** : `analyze_ae(text, project_id=None)`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_analyze_ae_nominal_structure
   - Mock retourne : prix, penalites, garanties, clauses_risquees
   - Assert : structure complete

2. test_analyze_ae_empty_text
   - Input : ""
   - Expected : resultat vide

3. test_analyze_ae_prix_global_forfaitaire
   - Mock : type_prix="global_et_forfaitaire", montant=500000
   - Assert : prix parse correctement

4. test_analyze_ae_penalites_retard
   - Mock : penalites taux 1/1000 par jour
   - Assert : penalites flaggees

5. test_analyze_ae_garantie_performance
   - Mock : garantie a premiere demande 5%
   - Assert : garantie detectee et evaluee

6. test_analyze_ae_revision_prix_absente
   - Mock : aucune clause de revision
   - Assert : risque signale

7. test_analyze_ae_jurisprudence_injected
   - Capture system_prompt
   - Assert : contexte jurisprudence present

8. test_analyze_ae_llm_error_handled
   - Mock LLM raise
   - Expected : gestion erreur propre
```

---

### test_conflict_detector.py
**Fichier source** : `apps/api/app/services/conflict_detector.py`
**Fonctions testees** : `detect_conflicts(texts, project_id)`, `_build_documents_block()`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_detect_conflicts_nominal_5_categories
   - Input : texts={"rc": "...", "ccap": "...", "cctp": "..."}
   - Mock LLM retourne conflits delai + montant + exigence
   - Assert : conflits categorises par type

2. test_detect_conflicts_no_conflicts
   - Mock LLM retourne {"conflicts": []}
   - Assert : liste vide, pas de faux positifs

3. test_detect_conflicts_delai_mismatch
   - Mock : RC dit 6 mois, CCAP dit 180 jours ouvres
   - Assert : conflit type="delai" severity="high"

4. test_detect_conflicts_montant_mismatch
   - Mock : DPGF 150m2 vs CCTP 200m2
   - Assert : conflit type="montant"

5. test_detect_conflicts_exigence_contradictoire
   - Mock : RC variantes autorisees vs AE variantes interdites
   - Assert : conflit type="exigence" severity="critical"

6. test_detect_conflicts_clause_illegale
   - Mock : penalites > 1/1000
   - Assert : conflit type="clause_illegale"

7. test_detect_conflicts_reference_invalide
   - Mock : CCTP reference article CCAP inexistant
   - Assert : conflit type="reference"

8. test_build_documents_block_truncation
   - Input : texte tres long > max_chars_per_doc
   - Assert : texte tronque

9. test_detect_conflicts_cctp_dpgf_cross_doc
   - Mock : conflit type="cctp_dpgf" (materiaux vs quantites)
   - Assert : conflit cross-doc detecte

10. test_detect_conflicts_empty_texts
    - Input : texts={}
    - Expected : resultat vide, LLM non appele

11. test_detect_conflicts_single_doc
    - Input : texts={"rc": "..."}
    - Expected : pas de conflits inter-documents (ou warn)
```

---

### test_subcontracting_analyzer.py
**Fichier source** : `apps/api/app/services/subcontracting_analyzer.py`
**Fonction testee** : `analyze_subcontracting(project_id, db)`
**Fixtures** : `mock_llm`, `db_session`, `mock_embedder`

```
Tests a implementer :

1. test_analyze_subcontracting_nominal
   - Setup : projet avec RC + CCTP + CompanyProfile en DB
   - Mock LLM retourne lots_analysis + conflits
   - Assert : structure JSON valide

2. test_subcontracting_autorisee_flag
   - Mock : sous_traitance_autorisee=true
   - Assert : flag correct

3. test_subcontracting_interdite_mais_competence_manquante
   - Mock : RC interdit, entreprise manque competence electricite
   - Assert : conflit severity="high"

4. test_paiement_direct_seuil_600
   - Mock : seuil_paiement_direct_eur=600
   - Assert : paiement_direct_applicable=true

5. test_lots_analysis_competence_interne
   - Mock : lot gros oeuvre competence_interne=true
   - Assert : sous_traitance_recommandee=false

6. test_lots_analysis_competence_externe
   - Mock : lot electricite competence_interne=false
   - Assert : sous_traitance_recommandee=true

7. test_score_risque_50pct_lots_soustraites
   - Mock : > 50% lots en sous-traitance
   - Assert : score_risque > 70

8. test_no_company_profile
   - Setup : pas de CompanyProfile en DB
   - Expected : analyse avec profil "inconnu"

9. test_no_rc_text
   - Setup : pas de document RC
   - Expected : restrictions_rc vide, confidence faible
```

---

### test_questions_generator.py
**Fichier source** : `apps/api/app/services/questions_generator.py`
**Fonction testee** : `generate_questions(context, summary, project_id)`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_generate_questions_nominal_5_to_10
   - Mock LLM retourne 7 questions
   - Assert : len(questions) entre 5 et 10

2. test_questions_have_priority
   - Mock : chaque question a priority in (CRITIQUE, HAUTE, MOYENNE, BASSE)
   - Assert : toutes les priorites valides

3. test_questions_reference_documents
   - Mock : question cite "CCTP article 3.2.1"
   - Assert : reference_document present

4. test_questions_sorted_by_priority
   - Mock : CRITIQUE en premier
   - Assert : ordre decroissant de priorite

5. test_questions_empty_context
   - Input : context=""
   - Expected : liste vide ou questions generiques

6. test_questions_pydantic_validation
   - Mock : donnees invalides
   - Expected : ValidatedQuestions normalise

7. test_questions_llm_failure
   - Mock LLM raise
   - Expected : erreur geree
```

---

### test_scoring_simulator.py
**Fichier source** : `apps/api/app/services/scoring_simulator.py`
**Fonctions testees** : `simulate_scoring()`, `_format_criteria_section()`, `_format_company_section()`
**Fixtures** : `mock_llm`

```
Tests a implementer :

1. test_simulate_scoring_nominal
   - Input : criteria_payload avec prix 60% + technique 40%
   - Mock LLM retourne notes + classement
   - Assert : note_globale entre 0 et 20

2. test_scoring_note_technique_ponderation
   - Mock : 3 criteres techniques avec notes et poids
   - Assert : note_technique = moyenne ponderee

3. test_scoring_classement_top3
   - Mock : note_globale=16.5
   - Assert : classement="Top 3"

4. test_scoring_classement_risque
   - Mock : note_globale=8.0
   - Assert : classement="Risque"

5. test_scoring_axes_amelioration
   - Mock : 3 recommandations
   - Assert : len(axes) >= 3

6. test_scoring_without_company_profile
   - Input : company_profile=None
   - Expected : simulation avec candidat moyen

7. test_format_criteria_section_empty
   - Input : criteria_payload={}
   - Expected : texte par defaut

8. test_format_company_section_full
   - Input : profil complet (CA, effectif, certifs)
   - Assert : toutes les infos presentes dans le texte

9. test_scoring_pydantic_validation
   - Mock : donnees invalides
   - Expected : ValidatedScoringSimulation normalise
```

---

### test_btp_pricing.py (PRIORITE HAUTE — calculs mathematiques)
**Fichier source** : `apps/api/app/services/btp_pricing.py`
**Fonctions testees** : toutes (14 fonctions, aucun mock LLM necessaire)
**Fixtures** : aucun (module statique)

```
Tests a implementer :

--- get_price_index ---
1. test_get_price_index_bt01_found
   - Input : "BT01"
   - Expected : PriceIndexTemplate avec code="BT01", base_value=118.2

2. test_get_price_index_unknown_returns_none
   - Input : "INVALID"
   - Expected : None

3. test_get_price_index_case_insensitive
   - Input : "bt01"
   - Expected : trouve BT01

--- apply_price_adjustment ---
4. test_apply_price_adjustment_bt01_formula
   - Input : prix_initial=100, index_code="BT01", base_value=118.2, current_value=127.7
   - Expected : P = 100 * (0.15 + 0.85 * (127.7 / 118.2)) = 100 * (0.15 + 0.85*1.0804) = 100 * 1.0683 = 106.83 (approx)
   - Assert : abs(result - 106.83) < 0.5

5. test_apply_price_adjustment_zero_base_value
   - Input : base_value=0
   - Expected : erreur ou retourne prix initial sans ajustement

6. test_apply_price_adjustment_negative_prix
   - Input : prix_initial=-100
   - Expected : gere correctement (retourne negatif ou erreur)

7. test_apply_price_adjustment_all_indexes
   - Parametrize sur BT01, TP01, TP02, TP10a, TP09
   - Assert : resultat > 0 pour chaque indice

--- detect_revision_formula ---
8. test_detect_revision_formula_standard
   - Input : "P = P0 x [0.15 + 0.85 x (BT01n / BT01_0)]"
   - Expected : {"part_fixe": 0.15, "part_variable": 0.85, "index_code": "BT01"}

9. test_detect_revision_formula_custom_parts
   - Input : "P = P0 x [0.20 + 0.80 x (TP01n / TP01_0)]"
   - Expected : part_fixe=0.20, part_variable=0.80

10. test_detect_revision_formula_no_formula
    - Input : "Aucune revision de prix prevue"
    - Expected : None

11. test_detect_revision_formula_multiple_indexes
    - Input : texte avec BT01 et TP02
    - Expected : detecte au moins un des deux

--- get_geo_coefficient ---
12. test_geo_coefficient_ile_de_france
    - Input : "ile-de-france"
    - Expected : coefficient > 1.0 (majoration IDF)

13. test_geo_coefficient_province
    - Input : "bretagne"
    - Expected : coefficient ~1.0

14. test_geo_coefficient_unknown_region
    - Input : "atlantis"
    - Expected : coefficient par defaut (1.0)

--- get_pricing_reference ---
15. test_pricing_reference_beton
    - Input : "beton arme"
    - Expected : liste non vide avec prix min/max

16. test_pricing_reference_electricite
    - Input : "electricite"
    - Expected : au moins 1 resultat

17. test_pricing_reference_no_match
    - Input : "zzzzzzz_invalid"
    - Expected : liste vide

18. test_pricing_reference_case_insensitive
    - Input : "PEINTURE"
    - Expected : trouve les entrees peinture

--- check_dpgf_pricing ---
19. test_check_dpgf_pricing_nominal
    - Input : [{"designation": "Beton C25/30", "prix_unitaire": 180, "unite": "m3"}]
    - Expected : status in ("normal", "sous-evalue", "surevalue")

20. test_check_dpgf_pricing_sous_evalue
    - Input : prix a 50% de la fourchette basse
    - Expected : status="sous-evalue"

21. test_check_dpgf_pricing_surevalue
    - Input : prix a 200% de la fourchette haute
    - Expected : status="surevalue"

22. test_check_dpgf_pricing_with_region
    - Input : region="ile-de-france"
    - Expected : fourchettes ajustees par coefficient regional

23. test_check_dpgf_pricing_empty_rows
    - Input : []
    - Expected : liste vide

24. test_check_dpgf_pricing_missing_prix
    - Input : [{"designation": "Beton", "prix_unitaire": None}]
    - Expected : gere gracieusement

--- PRICE_ADJUSTMENT_2026 ---
25. test_price_adjustment_coefficient_value
    - Assert : PRICE_ADJUSTMENT_2026 == 1.08

--- get_pricing_summary ---
26. test_get_pricing_summary_returns_stats
    - Assert : dict avec total_entries > 0, categories > 0

--- _match_score ---
27. test_match_score_exact_match
    - Input : query_words=["beton"], entry avec keywords incluant "beton"
    - Expected : score eleve (> 0.8)

28. test_match_score_partial_match
    - Input : query_words=["beton", "arme", "xyz"]
    - Expected : score moyen (proportionnel aux mots trouves)

--- _parse_price ---
29. test_parse_price_float
    - Input : 150.50
    - Expected : 150.50

30. test_parse_price_string_with_euro
    - Input : "150,50 EUR"
    - Expected : 150.50

31. test_parse_price_invalid
    - Input : "N/A"
    - Expected : None

--- get_all_price_indexes ---
32. test_get_all_price_indexes_returns_5
    - Assert : len(result) == 5 (BT01, TP01, TP02, TP10a, TP09)
    - Assert : chaque index a code, nom, base_value, latest_value
```

---

### test_cashflow_simulator_extended.py (enrichir l'existant)
**Fichier source** : `apps/api/app/services/cashflow_simulator.py`
**Fonctions testees** : `simulate_cashflow()`, `_compute_production_weights()`, `_empty_result()`
**Fixtures** : aucun (calculs purs)

```
Tests a ajouter (en plus de test_cashflow.py existant) :

1. test_cashflow_avance_forfaitaire_5pct
   - Input : montant=1_000_000, avance_pct=5
   - Assert : mois 1 avance = 50_000

2. test_cashflow_retenue_garantie_5pct
   - Input : retenue_garantie_pct=5
   - Assert : chaque mois la retenue est deduite du paiement

3. test_cashflow_penalites_retard
   - Input : penalites_jour=500, jours_retard=10
   - Assert : total penalites = 5_000

4. test_cashflow_bfr_calculation
   - Assert : BFR = decaissements cumules - encaissements cumules (positif = besoin)

5. test_cashflow_12_months
   - Input : duree_mois=12, montant=1_200_000
   - Assert : 12 CashFlowMonth retournes

6. test_cashflow_zero_montant
   - Input : montant=0
   - Expected : _empty_result ou all zeros

7. test_cashflow_production_weights_sum_to_1
   - Input : duree_mois=6
   - Assert : sum(weights) == 1.0 (a epsilon pres)

8. test_cashflow_delai_paiement_30j
   - Input : delai_paiement_jours=30
   - Assert : encaissement decale de 1 mois

9. test_cashflow_delai_paiement_60j
   - Input : delai_paiement_jours=60
   - Assert : encaissement decale de 2 mois

10. test_empty_result_has_reason
    - Input : reason="montant nul"
    - Assert : result["reason"] == "montant nul"
```

---

### test_gonogo_advanced_extended.py (enrichir l'existant)
**Fichier source** : `apps/api/app/services/gonogo_advanced.py`
**Fonctions testees** : `compute_profile_match()`, `enrich_gonogo_with_profile()`, helpers
**Fixtures** : `db_session`

```
Tests a ajouter :

1. test_9_dimensions_all_present
   - Input : profil complet
   - Assert : 9 dimensions dans le resultat

2. test_region_match_exact
   - Company regions=["Ile-de-France"], market_location="Paris 75001"
   - Assert : _region_match == True

3. test_region_match_no_match
   - Company regions=["Bretagne"], market_location="Lyon"
   - Assert : _region_match == False

4. test_certif_overlap_all_matched
   - Company certs=["Qualibat 7131", "RGE"], required=["Qualibat 7131"]
   - Assert : overlap count=1

5. test_certif_overlap_none_matched
   - Company certs=["ISO 9001"], required=["Qualibat 7131"]
   - Assert : overlap count=0

6. test_certif_normalize_case
   - _normalize_certification("qualibat  7131") == "qualibat 7131"

7. test_parse_int_valid
   - _parse_int("42") == 42

8. test_parse_int_none
   - _parse_int(None) == None

9. test_parse_int_string
   - _parse_int("abc") == None

10. test_enrich_gonogo_no_profile
    - Input : pas de CompanyProfile en DB
    - Expected : gonogo retourne sans enrichissement

11. test_score_seuils_go_nogo
    - Score >= 60 => "GO", Score < 40 => "NO-GO", entre => "A ETUDIER"
```

---

### test_exporter.py
**Fichier source** : `apps/api/app/services/exporter.py`
**Fonctions testees** : `generate_export_pdf()`, `generate_export_docx()`, `generate_memo_technique()`
**Fixtures** : `db_session` (avec projet + resultats mock en DB)

```
Tests a implementer :

1. test_generate_pdf_returns_bytes
   - Setup : projet avec summary + checklist + criteria en DB
   - Assert : result is bytes, len(result) > 100

2. test_generate_pdf_valid_pdf_header
   - Assert : result[:5] == b"%PDF-"

3. test_generate_pdf_empty_project
   - Setup : projet sans resultats
   - Expected : PDF genere (avec sections vides)

4. test_generate_docx_returns_bytes
   - Setup : projet avec resultats
   - Assert : result is bytes, len(result) > 100

5. test_generate_docx_valid_docx_header
   - Assert : result[:2] == b"PK" (ZIP/DOCX magic bytes)

6. test_generate_docx_contains_sections
   - Assert : docx contient les sections Resume, Checklist, Criteres

7. test_generate_memo_technique_returns_bytes
   - Setup : projet avec profil entreprise
   - Assert : len(result) > 100, result[:2] == b"PK"

8. test_generate_pdf_with_all_analysis_types
   - Setup : projet avec les 15 types d'analyse
   - Assert : PDF genere sans erreur, taille > PDF minimal

9. test_generate_pdf_unicode_handling
   - Setup : titre projet avec accents et emojis
   - Assert : pas d'erreur d'encodage

10. test_generate_pdf_project_not_found
    - Input : project_id inexistant
    - Expected : raise HTTPException(404) ou retourne None
```

---

### test_webhook_dispatch_extended.py (enrichir l'existant)
**Fichier source** : `apps/api/app/services/webhook_dispatch.py`
**Fonctions testees** : `_is_safe_url()`, `_sign_payload()`, `dispatch_event()`
**Fixtures** : `db_session`

```
Tests a ajouter :

1. test_is_safe_url_https_valid
   - Input : "https://example.com/webhook"
   - Expected : True

2. test_is_safe_url_localhost_blocked
   - Input : "http://127.0.0.1/hook"
   - Expected : False

3. test_is_safe_url_10_network_blocked
   - Input : "http://10.0.0.1/hook"
   - Expected : False

4. test_is_safe_url_172_16_blocked
   - Input : "http://172.16.0.1/hook"
   - Expected : False

5. test_is_safe_url_192_168_blocked
   - Input : "http://192.168.1.1/hook"
   - Expected : False

6. test_is_safe_url_ipv6_loopback_blocked
   - Input : "http://[::1]/hook"
   - Expected : False

7. test_is_safe_url_link_local_blocked
   - Input : "http://169.254.1.1/hook"
   - Expected : False

8. test_is_safe_url_no_scheme
   - Input : "example.com/hook"
   - Expected : False

9. test_sign_payload_hmac_sha256
   - Input : payload="test", secret="mysecret"
   - Assert : resultat == hmac.new(secret, payload, sha256).hexdigest()

10. test_sign_payload_deterministic
    - Deux appels memes inputs
    - Assert : memes resultats

11. test_dispatch_event_success
    - Mock httpx.post retourne 200
    - Assert : delivery cree en DB avec status="delivered"

12. test_dispatch_event_failure_retry
    - Mock httpx.post retourne 500
    - Assert : delivery cree avec status="failed"

13. test_dispatch_event_max_failures_disables
    - Setup : endpoint avec failure_count=10
    - Assert : dispatch_event ne tente pas l'envoi
```

---

### test_language_detect.py
**Fichier source** : `apps/api/app/services/language_detect.py`
**Fonctions testees** : `detect_language(text)`, `detect_project_language(db, project_id)`
**Fixtures** : `db_session`

```
Tests a implementer :

1. test_detect_language_french_text
   - Input : "Le marche public de travaux concerne la construction d'un gymnase"
   - Expected : "fr"

2. test_detect_language_english_text
   - Input : "The public procurement tender concerns construction of a gymnasium"
   - Expected : "en"

3. test_detect_language_mixed_text
   - Input : texte moitie FR moitie EN
   - Expected : langue dominante

4. test_detect_language_empty_text
   - Input : ""
   - Expected : "fr" (defaut)

5. test_detect_language_short_text
   - Input : "OK" (trop court pour determiner)
   - Expected : "fr" (defaut)

6. test_detect_language_numbers_only
   - Input : "123 456 789"
   - Expected : "fr" (defaut)

7. test_detect_project_language_from_docs
   - Setup : projet avec documents FR en DB
   - Assert : "fr"

8. test_detect_project_language_no_docs
   - Setup : projet sans documents
   - Expected : "fr" (defaut)
```

---

### test_dc_checker.py
**Fichier source** : `apps/api/app/services/dc_checker.py`
**Fonctions testees** : `normalize_ocr_references(text)`, `analyze_dc_requirements(text, project_id)`
**Fixtures** : `mock_llm`

```
Tests a implementer :

--- normalize_ocr_references ---
1. test_normalize_dc1_with_spaces
   - Input : "D C1"
   - Expected : "DC1"

2. test_normalize_dc1_confusion_l_1
   - Input : "DCl"
   - Expected : "DC1"

3. test_normalize_dc2
   - Input : "D C 2"
   - Expected : "DC2"

4. test_normalize_kbis_garbled
   - Input : "K b i s"
   - Expected : "Kbis"

5. test_normalize_urssaf_garbled
   - Input : "U R S S A F"
   - Expected : "URSSAF"

6. test_normalize_qualibat_garbled
   - Input : "Qua1ibat"
   - Expected : "Qualibat"

7. test_normalize_iso_with_number
   - Input : "I S O 9001"
   - Expected : "ISO 9001"

8. test_normalize_attri1
   - Input : "A T T R I 1"
   - Expected : "ATTRI1"

9. test_normalize_clean_text_unchanged
   - Input : "Le DC1 est requis"
   - Expected : "Le DC1 est requis"

--- analyze_dc_requirements ---
10. test_analyze_dc_nominal
    - Mock LLM retourne liste documents requis (DC1, DC2, Kbis, URSSAF)
    - Assert : structure valide

11. test_analyze_dc_empty_text
    - Input : ""
    - Expected : resultat vide

12. test_analyze_dc_all_documents_found
    - Mock : status=OK pour tous les documents
    - Assert : aucune alerte

13. test_analyze_dc_missing_documents
    - Mock : DC1 status=MANQUANT
    - Assert : alerte presente

14. test_analyze_dc_expired_documents
    - Mock : Kbis date > 3 mois
    - Assert : alerte perime

15. test_analyze_dc_pydantic_validation
    - Mock : donnees invalides
    - Expected : ValidatedDcCheck normalise
```

---

### test_retriever.py
**Fichier source** : `apps/api/app/services/retriever.py`
**Fonctions testees** : `retrieve_relevant_chunks()`, `retrieve_hybrid()`, `format_context()`, `get_max_similarity()`, `expand_query()`, `rerank_with_llm()`
**Fixtures** : `db_session`, `mock_embedder`

```
Tests a implementer :

1. test_retrieve_no_chunks_returns_empty
   - Setup : DB vide (pas de chunks)
   - Assert : [] retourne, embed_query NON appele

2. test_retrieve_with_chunks_returns_sorted
   - Setup : chunks en DB avec embeddings (SQLite fallback)
   - Note : test avec _fallback_text_chunks car pgvector pas dispo en SQLite
   - Assert : liste non vide

3. test_format_context_nominal
   - Input : [{"content": "texte1", "doc_name": "RC.pdf"}, ...]
   - Assert : string formattee avec separateurs

4. test_format_context_empty
   - Input : []
   - Expected : "" ou "Aucun contexte"

5. test_get_max_similarity_nominal
   - Input : [{"similarity": 0.9}, {"similarity": 0.7}, {"similarity": 0.5}]
   - Expected : 0.9

6. test_get_max_similarity_empty
   - Input : []
   - Expected : 0.0

7. test_expand_query_adds_synonyms
   - Input : "penalites retard"
   - Expected : liste avec variations (penalites, retard, delai, etc.)

8. test_similarity_threshold_filtering
   - Assert : SIMILARITY_THRESHOLD == 0.50

9. test_fallback_text_chunks_bm25
   - Setup : chunks en DB sans embeddings
   - Assert : _fallback_text_chunks retourne des resultats bases sur texte

10. test_rerank_with_llm_mock
    - Mock LLM pour reranking
    - Assert : resultats reordonne
```

---

### test_llm_service.py
**Fichier source** : `apps/api/app/services/llm.py`
**Fonctions testees** : `LLMService.complete_json()`, `_build_system_blocks()`
**Fixtures** : mock Anthropic SDK

```
Tests a implementer :

1. test_complete_json_nominal
   - Mock anthropic.messages.create retourne JSON valide
   - Assert : dict retourne

2. test_complete_json_invalid_json_repaired
   - Mock retourne JSON malformed (trailing comma)
   - Assert : JSON repare et parse

3. test_complete_json_required_keys_missing
   - Mock retourne {"a": 1} mais required_keys=["a", "b"]
   - Expected : raise ValueError

4. test_complete_json_required_keys_present
   - Mock retourne {"a": 1, "b": 2}, required_keys=["a", "b"]
   - Assert : pas d'erreur

5. test_complete_json_pydantic_validator
   - Mock retourne donnees invalides
   - Validator corrige les valeurs
   - Assert : resultat normalise

6. test_complete_json_retry_on_rate_limit
   - Mock : 1er appel raise RateLimitError, 2eme OK
   - Assert : retourne resultat du 2eme appel

7. test_complete_json_circuit_breaker
   - Mock : 5 erreurs consecutives
   - Assert : CircuitBreakerError raised au 6eme

8. test_build_system_blocks_with_cache
   - Input : cache=True
   - Assert : retourne liste avec cache_control ephemeral

9. test_build_system_blocks_without_cache
   - Input : cache=False
   - Assert : retourne string brut

10. test_complete_json_timeout
    - Mock : raise APITimeoutError
    - Assert : retry tente (tenacity)

11. test_usage_tracking
    - Mock : retourne response avec usage
    - Assert : _usage_accumulator incremente
```

---

### test_verification.py
**Fichier source** : `apps/api/app/services/verification.py`
**Fonction testee** : `verify_cross_analysis_consistency(project_id, results)`
**Fixtures** : aucun (fonction pure)

```
Tests a implementer :

1. test_verify_no_issues
   - Input : results coherents (dates identiques, scores coherents)
   - Assert : issues=[], score=100, status="verified"

2. test_verify_date_mismatch
   - Input : summary.deadline_submission != timeline.submission_deadline
   - Assert : issue type="date_mismatch" severity="high"

3. test_verify_gonogo_score_inconsistent
   - Input : gonogo score=85 mais breakdown donne 50
   - Assert : issue type="score_mismatch"

4. test_verify_criteria_weights_not_100
   - Input : criteres poids 60% + 30% = 90%
   - Assert : issue type="weight_inconsistency"

5. test_verify_empty_results
   - Input : results={}
   - Assert : score=100, no issues (rien a verifier)

6. test_verify_partial_results
   - Input : only summary present
   - Assert : verifie ce qui est disponible, pas d'erreur
```

---

### test_analyzer_orchestrator.py
**Fichier source** : `apps/api/app/services/analyzer.py`
**Fonctions testees** : `run_full_analysis()`, `check_dce_completeness()`, helpers
**Fixtures** : `db_session`, `mock_llm`, `mock_embedder`, `mock_storage`

```
Tests a implementer :

1. test_check_dce_completeness_all_present
   - Setup : documents RC, CCAP, CCTP, DPGF en DB
   - Assert : completeness score eleve

2. test_check_dce_completeness_missing_rc
   - Setup : pas de RC
   - Assert : alerte "RC manquant"

3. test_run_full_analysis_minimal
   - Setup : 1 document type "rc" avec texte
   - Mock : tous les LLM calls
   - Assert : summary, checklist, criteria generes

4. test_save_result_creates_extraction_result
   - Setup : appel _save_result
   - Assert : ExtractionResult cree en DB

5. test_get_doc_text_by_type
   - Setup : 2 docs (RC + CCAP) en DB
   - Assert : _get_doc_text_by_type retourne le bon texte

6. test_parse_montant_valid
   - _parse_montant("500 000 EUR") == 500000

7. test_parse_montant_none
   - _parse_montant(None) == None

8. test_ocr_quality_warning
   - Setup : avg OCR < 40%
   - Assert : warning dans le resultat
```

---

### test_chunker.py
**Fichier source** : `apps/api/app/services/chunker.py`
**Fonctions testees** : `chunk_pages()`, `count_tokens()`, `contextualize_chunk()`, `chunk_by_structure()`
**Fixtures** : aucun (fonctions pures)

```
Tests a implementer :

1. test_chunk_pages_nominal
   - Input : 3 pages de 500 tokens chacune
   - Assert : chunks crees, chaque chunk < 800 tokens

2. test_chunk_pages_overlap
   - Assert : chunks adjacents partagent ~150 tokens

3. test_count_tokens_nominal
   - Input : "hello world"
   - Assert : result > 0

4. test_count_tokens_empty
   - Input : ""
   - Assert : 0

5. test_contextualize_chunk_ccap
   - Input : doc_type="ccap", doc_name="CCAP.pdf"
   - Assert : prefix contient "[CCAP: CCAP.pdf"

6. test_contextualize_chunk_rc
   - Input : doc_type="rc"
   - Assert : prefix contient "[RC:"

7. test_chunk_by_structure_articles
   - Input : texte avec "Article 1" ... "Article 2"
   - Assert : chunks decoupes aux frontieres d'articles

8. test_chunk_pages_empty
   - Input : pages=[]
   - Assert : []

9. test_chunk_size_constant
   - Assert : CHUNK_SIZE == 800 et CHUNK_OVERLAP == 150
```

---

### test_dpgf_extractor.py
**Fichier source** : `apps/api/app/services/dpgf_extractor.py`
**Fonctions testees** : `extract_tables_from_pdf()`, `generate_excel()`, `extract_dpgf()`, helpers
**Fixtures** : mock pdfplumber

```
Tests a implementer :

1. test_normalize_col_name_designation
   - Input : "Designation des travaux"
   - Expected : "designation"

2. test_normalize_col_name_prix_unitaire
   - Input : "Prix Unit."
   - Expected : "prix_unitaire"

3. test_normalize_col_name_unknown
   - Input : "xyz_random"
   - Expected : None

4. test_parse_number_float
   - Input : "1 234,56"
   - Expected : 1234.56

5. test_parse_number_invalid
   - Input : "N/A"
   - Expected : None

6. test_generate_excel_returns_bytes
   - Input : tables avec quelques lignes
   - Assert : bytes retourne, len > 0

7. test_generate_excel_valid_xlsx
   - Assert : result[:2] == b"PK" (ZIP header)

8. test_is_header_row_true
   - Input : ["N", "Designation", "Unite", "Qte", "PU"]
   - Expected : True

9. test_is_header_row_false
   - Input : ["1", "Beton", "m3", "100", "150"]
   - Expected : False

10. test_extract_dpgf_integration
    - Mock pdfplumber retourne tables
    - Assert : ExtractedTable avec rows
```

---

### test_analytics.py
**Fichier source** : `apps/api/app/services/analytics.py`
**Fonctions testees** : `get_org_stats()`, `get_org_activity()`
**Fixtures** : `db_session`

```
Tests a implementer :

1. test_get_org_stats_empty_org
   - Setup : org sans projets
   - Assert : total_projects=0

2. test_get_org_stats_with_projects
   - Setup : 3 projets (draft, analyzing, ready)
   - Assert : total_projects=3, projects_by_status correct

3. test_get_org_stats_documents_count
   - Setup : projets avec documents
   - Assert : total_documents correct

4. test_get_org_activity_30_days
   - Setup : activite sur 30 jours
   - Assert : liste de 30 entrees

5. test_get_org_activity_empty
   - Setup : aucune activite
   - Assert : liste vide ou zeros
```

---

### test_boamp_watcher.py
**Fichier source** : `apps/api/app/services/boamp_watcher.py`
**Fonctions testees** : `_build_query_params()`, `_normalize_record()`, `fetch_boamp_results()`
**Fixtures** : mock httpx

```
Tests a implementer :

1. test_build_query_params_minimal
   - Input : config avec keyword="batiment"
   - Assert : params contient q="batiment"

2. test_normalize_record_full
   - Input : record BOAMP brut
   - Assert : champs normalises (title, date, value, etc.)

3. test_parse_date_valid
   - Input : "2026-03-15"
   - Expected : datetime

4. test_parse_date_invalid
   - Input : "not-a-date"
   - Expected : None

5. test_parse_value_integer
   - Input : 500000
   - Expected : 500000

6. test_fetch_boamp_results_mock
   - Mock httpx GET retourne JSON BOAMP
   - Assert : liste de records normalises
```

---

## PARTIE 2 — TEST E2E PIPELINE COMPLET

### test_e2e_pipeline.py
**Fichier** : `apps/api/tests/test_e2e_pipeline.py`

```python
"""Test E2E du pipeline complet : projet -> upload -> extraction -> analyse -> export.

Utilise une vraie DB SQLite en memoire avec mocks LLM/Storage/Embedder.
Temps d'execution cible : < 30s.
"""

# ═══ FIXTURES ═══

# fixture pdf_bytes : PDF minimal valide (PyMuPDF genere)
# fixture mock_all_llm_responses : dict mapant chaque type d'analyse a une reponse JSON fixe
#   - summary, checklist, criteria, gonogo, timeline, ccap, rc, ae, cctp,
#     conflicts, questions, scoring, dc_check, subcontracting, cashflow, memo
# fixture mock_storage_service : LocalStorageService en tmpdir
# fixture mock_embedder : retourne [0.1]*1536 pour tout

# ═══ ETAPES DU TEST ═══

async def test_full_pipeline_e2e(db_session, mock_all_llm_responses, mock_storage, mock_embedder):
    """
    Etape 1 : Creer organisation + utilisateur
    - Assert : org et user en DB

    Etape 2 : Creer projet
    - POST /api/v1/projects {"title": "Test E2E - Construction gymnase"}
    - Assert : 201, project_id retourne

    Etape 3 : Upload 3 documents (RC, CCAP, CCTP)
    - POST /api/v1/projects/{id}/documents (multipart)
    - Mock storage.upload_bytes
    - Assert : 3 documents crees en DB

    Etape 4 : Extraction texte (simule process_document)
    - Appel direct pdf_extractor.extract_text(pdf_bytes)
    - Assert : pages extraites, texte non vide

    Etape 5 : Chunking
    - Appel chunker.chunk_pages(pages)
    - Assert : chunks crees, taille < 800 tokens

    Etape 6 : Embeddings
    - Mock embed_texts retourne vecteurs
    - Assert : chunks avec embeddings en DB

    Etape 7 : Analyse complete
    - Appel analyzer.run_full_analysis(db, project_id)
    - Mock chaque LLM call avec reponses predefinies
    - Assert : 15+ ExtractionResult en DB (summary, checklist, criteria, ccap, rc, ae,
      cctp, conflicts, questions, scoring, gonogo, timeline, dc_check, subcontracting, cashflow)

    Etape 8 : Verification resultats
    - Chaque resultat : payload non vide, structure JSON valide
    - Summary : project_overview present
    - Checklist : >= 1 item
    - Criteria : eligibility_conditions ou scoring_criteria present

    Etape 9 : Export PDF
    - Appel exporter.generate_export_pdf(db, project_id)
    - Assert : bytes retourne, > 1000 octets, commence par %PDF-

    Etape 10 : Export DOCX
    - Appel exporter.generate_export_docx(db, project_id)
    - Assert : bytes retourne, > 1000 octets, commence par PK

    Etape 11 : Export DPGF Excel
    - Mock pdfplumber pour tables
    - Assert : bytes Excel retourne

    Etape 12 : Verification cross-analysis
    - Appel verification.verify_cross_analysis_consistency()
    - Assert : score >= 0, status in ("verified", "warnings", "inconsistencies_found")
    """
    pass

async def test_pipeline_with_single_document(db_session, mock_all_llm_responses):
    """Verifie que le pipeline fonctionne avec un seul document (cas minimal)."""
    pass

async def test_pipeline_with_empty_document(db_session):
    """Verifie la gestion d'un document vide (0 texte extrait)."""
    pass

async def test_pipeline_ocr_low_quality(db_session, mock_all_llm_responses):
    """Verifie le warning si OCR avg < 40%."""
    pass
```

**Temps execution** : < 30s car tous les appels LLM et stockage sont mockes.
**Assertions cles** : 15 analyses produites, 3 exports valides, cross-check coherent.

---

## PARTIE 3 — TESTS FRONTEND (cible 50%)

### Setup commun (apps/web/src/test/setup.tsx)
Deja configure avec jsdom. A verifier :
- `@testing-library/react` installe
- `@testing-library/jest-dom` pour les matchers
- `msw` (Mock Service Worker) pour mocker l'API

---

### CcapRiskTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/CcapRiskTab.tsx`

```
1. test_renders_loading_skeleton_while_fetching
   - Mock useAnalysis retourne isLoading=true
   - Assert : AnalysisSkeleton visible

2. test_renders_error_alert_on_api_failure
   - Mock useAnalysis retourne error="Network error"
   - Assert : alert/banner d'erreur visible

3. test_renders_clauses_risquees_list
   - Mock data avec 3 clauses
   - Assert : 3 items rendus

4. test_renders_score_risque_global
   - Mock score=75
   - Assert : "75" visible, badge severity correcte

5. test_ai_disclaimer_present
   - Assert : composant AIDisclaimer rendered

6. test_confidence_warning_low
   - Mock confidence=0.3
   - Assert : ConfidenceWarning visible

7. test_clause_severity_badge_colors
   - Mock : clause CRITIQUE (rouge), HAUT (orange), MOYEN (jaune)
   - Assert : badges CSS correctes
```

---

### CctpAnalysisTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/CctpAnalysisTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_8_categories
   - Mock data avec 8 categories techniques
   - Assert : 8 sections rendues
4. test_renders_normes_references
5. test_renders_materiaux_specifications
6. test_ai_disclaimer_present
7. test_empty_data_shows_placeholder
```

---

### RcAnalysisTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/RcAnalysisTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_lots_list
4. test_renders_conditions_submission
5. test_renders_variantes_info
6. test_renders_groupement_info
7. test_ai_disclaimer_present
```

---

### AeAnalysisTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/AeAnalysisTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_prix_info
4. test_renders_penalites_section
5. test_renders_garanties_section
6. test_renders_clauses_risquees
7. test_ai_disclaimer_present
```

---

### ConflictsTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/ConflictsTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_conflicts_list
4. test_renders_severity_badges
5. test_renders_no_conflicts_message
6. test_conflict_detail_expandable
7. test_ai_disclaimer_present
```

---

### DcCheckTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/DcCheckTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_documents_checklist
4. test_renders_status_icons (OK, MANQUANT, EXPIRE)
5. test_renders_alerts_section
6. test_ai_disclaimer_present
```

---

### QuestionsTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/QuestionsTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_questions_list
4. test_renders_priority_badges
5. test_renders_copy_button
6. test_copy_question_to_clipboard
7. test_ai_disclaimer_present
```

---

### ScoringSimulatorTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/ScoringSimulatorTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_note_globale
4. test_renders_criteres_with_notes
5. test_renders_classement
6. test_renders_axes_amelioration
7. test_ai_disclaimer_present
```

---

### DpgfPricingTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/DpgfPricingTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_pricing_table
4. test_renders_status_indicators (sous-evalue, normal, surevalue)
5. test_renders_reference_prices
6. test_ai_disclaimer_present
```

---

### SubcontractingTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/SubcontractingTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_lots_analysis
4. test_renders_conflits_section
5. test_renders_score_risque
6. test_renders_recommendations
7. test_ai_disclaimer_present
```

---

### CashFlowTab.test.tsx
**Fichier source** : `apps/web/src/components/analysis/CashFlowTab.tsx`

```
1. test_renders_loading_state
2. test_renders_error_state
3. test_renders_chart (chart/table present)
4. test_renders_bfr_summary
5. test_renders_monthly_data
6. test_ai_disclaimer_present
```

---

### ProjectDetailPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/projects/[id]/page.tsx`

```
1. test_renders_17_tabs
   - Mock useProject retourne projet "ready"
   - Assert : 17 onglets affiches (Documents, Resume, Checklist, Criteres,
     CCAP, RC, AE, CCTP, Admin, Conflits, Questions, Scoring,
     Pricing, Tresorerie, Calendrier, Chat DCE, Export)

2. test_renders_loading_state
   - Mock useProject isLoading=true
   - Assert : skeleton visible

3. test_renders_404_not_found
   - Mock useProject error=404
   - Assert : message "Projet non trouve"

4. test_tab_navigation
   - Simulate click sur onglet "Checklist"
   - Assert : contenu checklist visible

5. test_tab_grouping_categories
   - Assert : 4 groupes visibles (Analyse, Technique, Finances, Export)

6. test_aria_attributes_on_tabs
   - Assert : role="tablist" sur container, role="tab" sur chaque onglet

7. test_project_title_displayed
   - Mock titre "Construction gymnase"
   - Assert : titre visible dans le header
```

---

### DashboardPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/dashboard/page.tsx`

```
1. test_renders_stats_cards
   - Mock stats (total_projects, projects_this_month)
   - Assert : cartes stats visibles

2. test_renders_empty_state_new_user
   - Mock : 0 projets
   - Assert : message "Premiers pas" visible

3. test_renders_recent_projects_list
   - Mock : 3 projets recents
   - Assert : 3 items rendus

4. test_renders_onboarding_steps
   - Mock : utilisateur nouveau
   - Assert : 3 etapes onboarding visibles
```

---

### PipelinePage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/pipeline/page.tsx`

```
1. test_renders_kanban_columns
   - Assert : colonnes draft, analyzing, ready, archived

2. test_renders_project_cards
   - Mock : projets dans chaque colonne
   - Assert : cartes visibles

3. test_empty_pipeline
   - Mock : 0 projets
   - Assert : message vide

4. test_drag_and_drop_interface
   - Assert : attributs drag handles presents
```

---

### VeillePage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/veille/page.tsx`

```
1. test_renders_search_filters
2. test_renders_results_list
3. test_renders_empty_results
4. test_filter_by_region
5. test_filter_by_montant
```

---

### LibraryPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/library/page.tsx`

```
1. test_renders_snippets_list
2. test_create_snippet
3. test_edit_snippet
4. test_delete_snippet
5. test_search_snippets
```

---

### BillingPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/billing/page.tsx`

```
1. test_renders_5_plan_cards
   - Assert : Gratuit, Starter 69EUR, Pro 179EUR, Europe 299EUR, Business 499EUR

2. test_current_plan_highlighted
   - Mock : plan=starter
   - Assert : carte starter a badge "Plan actuel"

3. test_checkout_button_disabled_for_current_plan

4. test_contact_button_for_europe_business
   - Assert : Europe et Business ont "Contactez-nous"

5. test_annual_discount_toggle
   - Click toggle annuel
   - Assert : prix affiches avec -20%

6. test_usage_meter_displayed
   - Mock : 12/15 docs utilises
   - Assert : barre progression visible
```

---

### SettingsCompanyPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/settings/company/page.tsx`

```
1. test_renders_company_form
2. test_submit_updates_profile
3. test_renders_certifications_field
4. test_renders_regions_field
```

---

### SettingsTeamPage.test.tsx
**Fichier source** : `apps/web/src/app/(dashboard)/settings/team/page.tsx`

```
1. test_renders_team_members_list
2. test_invite_member
3. test_remove_member
4. test_role_change
```

---

### ErrorBoundary.test.tsx
**Fichier source** : `apps/web/src/app/error.tsx`

```
1. test_renders_error_message
   - Simulate throw dans child component
   - Assert : message d'erreur visible

2. test_retry_button_works
   - Assert : bouton "Reessayer" present et fonctionnel

3. test_global_error_renders
   - Test global-error.tsx
```

---

### api.test.ts (interceptors)
**Fichier source** : `apps/web/src/lib/api.ts`

```
1. test_axios_adds_auth_header
   - Setup : token en store
   - Assert : Authorization: Bearer xxx

2. test_axios_timeout_30s_default
   - Assert : timeout config = 30000

3. test_token_refresh_on_401
   - Mock : 1er call retourne 401, refresh OK, retry OK
   - Assert : 2eme call reussi

4. test_token_refresh_race_condition
   - Mock : 3 calls simultanes, tous 401
   - Assert : 1 seul refresh, les 3 retry

5. test_failed_refresh_redirects_login
   - Mock : refresh echoue
   - Assert : redirect vers /login

6. test_llm_endpoints_120s_timeout
   - Assert : endpoints analyse ont timeout 120s
```

---

### useProjects.test.ts
**Fichier source** : `apps/web/src/hooks/useProjects.ts`

```
1. test_useProjects_returns_projects_list
2. test_useProjects_loading_state
3. test_useProjects_error_state
4. test_useProjects_stale_time_5min
5. test_useCreateProject_mutation
6. test_useDeleteProject_mutation
```

---

### useAnalysis.test.ts
**Fichier source** : `apps/web/src/hooks/useAnalysis.ts`

```
1. test_useAnalysis_returns_analysis_data
2. test_useAnalysis_loading_state
3. test_useAnalysis_error_state
4. test_useAnalysis_stale_time_5min
5. test_useTriggerAnalysis_mutation
```

---

### useDocuments.test.ts
**Fichier source** : `apps/web/src/hooks/useDocuments.ts`

```
1. test_useDocuments_returns_documents_list
2. test_useDocuments_upload_mutation
3. test_useDocuments_delete_mutation
```

---

### useGlossary.test.ts
**Fichier source** : `apps/web/src/hooks/useGlossary.ts`

```
1. test_useGlossary_returns_terms
2. test_useGlossary_search_filter
```

---

### auth.store.test.ts (enrichir l'existant)
**Fichier source** : `apps/web/src/stores/auth.ts`

```
Tests a ajouter :
1. test_login_stores_tokens
2. test_logout_clears_tokens
3. test_refresh_updates_token
4. test_isAuthenticated_computed
5. test_token_expiry_detection
```

---

### billing.store.test.ts
**Fichier source** : `apps/web/src/stores/billing.ts`

```
1. test_current_plan_getter
2. test_usage_data_getter
3. test_is_quota_exceeded
4. test_plan_features_by_tier
```

---

## PARTIE 4 — TESTS DE PERFORMANCE

### Configuration pytest-benchmark

**Fichier** : `apps/api/tests/test_benchmarks.py`

```
Dependances : pip install pytest-benchmark

--- Benchmarks backend ---

1. bench_rag_retrieval_10_chunks
   - Setup : 10 chunks en DB
   - Measure : retrieve_relevant_chunks()
   - Seuil : < 50ms (mocked embedder)

2. bench_rag_retrieval_100_chunks
   - Setup : 100 chunks
   - Seuil : < 100ms

3. bench_rag_retrieval_1000_chunks
   - Setup : 1000 chunks
   - Seuil : < 500ms

4. bench_llm_complete_json_overhead
   - Mock LLM retourne immediatement
   - Measure : overhead framework (parsing, validation)
   - Seuil : < 10ms

5. bench_chunker_500_pages
   - Input : 500 pages de texte
   - Measure : chunk_pages()
   - Seuil : < 2s

6. bench_export_pdf_10_pages
   - Measure : generate_export_pdf()
   - Seuil : < 3s

7. bench_export_pdf_50_pages
   - Seuil : < 10s

8. bench_btp_pricing_check_50_rows
   - Input : 50 lignes DPGF
   - Measure : check_dpgf_pricing()
   - Seuil : < 100ms

9. bench_conflict_detection_build_block
   - Input : 5 documents de 10000 chars
   - Measure : _build_documents_block()
   - Seuil : < 50ms

10. bench_full_analysis_pipeline
    - Mock tous les LLM
    - Measure : run_full_analysis()
    - Seuil : < 5s
```

### Configuration Locust (load testing)

**Fichier** : `apps/api/locustfile.py`

```python
# pip install locust

from locust import HttpUser, task, between

class AOCopilotUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        # Login et obtenir JWT
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "testpassword"
        })
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def list_projects(self):
        self.client.get("/api/v1/projects", headers=self.headers)

    @task(3)
    def get_project_detail(self):
        self.client.get("/api/v1/projects/{project_id}", headers=self.headers)

    @task(1)
    def trigger_analysis(self):
        self.client.post("/api/v1/analysis/{project_id}/trigger", headers=self.headers)

# Scenarios de charge :
# 1. locust -f locustfile.py --users 10 --spawn-rate 2 --run-time 60s
#    Cible : temps moyen < 5s analyse, P99 < 200ms projets
#
# 2. locust -f locustfile.py --users 50 --spawn-rate 10 --run-time 120s
#    Cible : 50 req/s sur /projects, P99 < 200ms
#
# 3. WebSocket test (separe) : 100 connexions simultanees chat DCE
```

### Metriques et seuils

| Metrique | Seuil | Outil |
|----------|-------|-------|
| RAG retrieval (10 chunks) | < 50ms | pytest-benchmark |
| RAG retrieval (1000 chunks) | < 500ms | pytest-benchmark |
| LLM overhead (mock) | < 10ms | pytest-benchmark |
| Export PDF (10 pages) | < 3s | pytest-benchmark |
| Full pipeline (mock) | < 5s | pytest-benchmark |
| API /projects P99 | < 200ms | Locust |
| API /projects throughput | > 50 req/s | Locust |
| 10 analyses simultanees | < 5s avg | Locust |
| 100 WebSocket connections | 0 crash | custom script |

---

## PARTIE 5 — TESTS DE SECURITE

### test_security.py
**Fichier** : `apps/api/tests/test_security.py`
**Fixtures** : `db_session`, `client`

```
Tests a implementer :

1. test_sql_injection_project_title
   - Input : titre = "'; DROP TABLE ao_projects; --"
   - POST /api/v1/projects {"title": "'; DROP TABLE ao_projects; --"}
   - Assert : 201 (titre stocke tel quel, pas d'injection)
   - Verify : table ao_projects toujours existante

2. test_xss_in_annotation_content
   - Input : content = "<script>alert('xss')</script>"
   - POST annotation avec ce contenu
   - Assert : contenu stocke mais echappe en sortie (ou sanitise)

3. test_csrf_protection
   - Envoyer POST sans CSRF token (si implemente)
   - Assert : 403 ou mecanisme CSRF verifie

4. test_rate_limit_enforced
   - Envoyer 11 requetes GET /api/v1/analysis/{id}/ccap en < 1 seconde
   - Assert : 11eme retourne 429 Too Many Requests

5. test_rls_cross_org_access
   - Setup : Org A avec projet, Org B avec user
   - User B tente GET /api/v1/projects/{org_a_project_id}
   - Assert : 403 ou 404

6. test_ssrf_webhook_localhost
   - Setup : webhook endpoint url="http://127.0.0.1/evil"
   - Trigger dispatch
   - Assert : bloque, pas d'envoi

7. test_ssrf_webhook_internal_ip
   - url="http://10.0.0.1/evil"
   - Assert : bloque

8. test_jwt_expired_token
   - Generer token avec exp = now - 1 minute
   - GET /api/v1/projects avec ce token
   - Assert : 401

9. test_jwt_invalid_signature
   - Generer token signe avec mauvaise cle
   - Assert : 401

10. test_file_upload_malicious_exe
    - Upload fichier .exe avec Content-Type application/pdf
    - Assert : rejete (magic bytes validation)

11. test_file_upload_oversized
    - Upload fichier > limite (ex: 100MB)
    - Assert : 413 ou 400

12. test_api_key_invalid
    - GET avec X-API-Key invalide
    - Assert : 401

13. test_password_hashing_not_plaintext
    - Verifier que le password en DB n'est pas en clair
    - Assert : hash bcrypt/argon2

14. test_signed_url_expiry
    - Generer signed URL, attendre expiry
    - Assert : URL expiree retourne 403

15. test_cors_headers
    - OPTIONS request avec Origin: http://evil.com
    - Assert : pas de Access-Control-Allow-Origin: http://evil.com
```

---

## PARTIE 6 — CONFIGURATION CI/CD

### Modifications a apporter a `.github/workflows/ci.yml`

```yaml
# ═══ BACKEND : ajouter pytest-cov ═══

    # Remplacer la step "Run pytest" existante (lignes 102-104) par :
    steps:
      # ... (steps existantes inchangees)

      - name: Install test dependencies
        working-directory: apps/api
        run: pip install pytest-cov pytest-benchmark

      - name: Run pytest with coverage
        working-directory: apps/api
        run: |
          pytest tests/ -v --tb=short \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=html:coverage-html \
            --cov-fail-under=60 \
            --benchmark-disable \
            -x
        # --cov-fail-under=60 : FAIL si couverture < 60%
        # --benchmark-disable : ne pas executer benchmarks en CI
        # -x : stop au premier echec

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage
          path: apps/api/coverage-html/
          retention-days: 14

      # Garder les steps Bandit et pip-audit existantes

# ═══ FRONTEND : ajouter vitest coverage ═══

  test-frontend:
    # ... (steps existantes inchangees)

      - name: Run Vitest with coverage
        working-directory: apps/web
        run: npx vitest run --coverage --coverage.reporter=text --coverage.reporter=html
        env:
          VITEST_COVERAGE_THRESHOLD_LINES: 40
          VITEST_COVERAGE_THRESHOLD_FUNCTIONS: 40
          VITEST_COVERAGE_THRESHOLD_BRANCHES: 30
          VITEST_COVERAGE_THRESHOLD_STATEMENTS: 40

      - name: Upload frontend coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: frontend-coverage
          path: apps/web/coverage/
          retention-days: 14

# ═══ BADGE COUVERTURE (nouveau job) ═══

  coverage-badge:
    name: Coverage Badge
    runs-on: ubuntu-latest
    needs: [test-backend]
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Download coverage artifact
        uses: actions/download-artifact@v4
        with:
          name: backend-coverage

      - name: Generate badge
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_TOKEN }}
          gistID: <GIST_ID>
          filename: ao-copilot-coverage.json
          label: coverage
          message: "60%+"
          color: green
```

### Modification vitest.config.ts (seuils de couverture)

```typescript
// Ajouter dans la section test.coverage :
coverage: {
  provider: "v8",
  reporter: ["text", "html", "lcov"],
  exclude: ["node_modules/", "src/test/", "**/*.d.ts", ".next/"],
  thresholds: {
    lines: 40,
    functions: 40,
    branches: 30,
    statements: 40,
  },
},
```

### Commandes exactes

```bash
# Backend - lancer les tests avec couverture
cd apps/api
pip install pytest-cov pytest-benchmark
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=60

# Backend - lancer les benchmarks
pytest tests/test_benchmarks.py -v --benchmark-only

# Frontend - lancer les tests avec couverture
cd apps/web
npm install -D @vitest/coverage-v8
npx vitest run --coverage

# Security tests only
cd apps/api
pytest tests/test_security.py -v

# E2E pipeline only
cd apps/api
pytest tests/test_e2e_pipeline.py -v -s

# Load tests
cd apps/api
pip install locust
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 60s --host http://localhost:8000
```

---

## RECAPITULATIF

### Fichiers de test a creer/enrichir

**Backend (19 nouveaux fichiers)** :
| Fichier | Tests | Priorite |
|---------|-------|----------|
| test_btp_pricing.py | 32 | P0 (calculs) |
| test_ccap_analyzer.py | 8 | P0 |
| test_cctp_analyzer.py | 8 | P0 |
| test_rc_analyzer.py | 8 | P0 |
| test_ae_analyzer.py | 8 | P0 |
| test_conflict_detector.py | 11 | P0 |
| test_dc_checker.py | 15 | P1 |
| test_retriever.py | 10 | P1 |
| test_llm_service.py | 11 | P1 |
| test_exporter.py | 10 | P1 |
| test_scoring_simulator.py | 9 | P1 |
| test_questions_generator.py | 7 | P1 |
| test_subcontracting_analyzer.py | 9 | P1 |
| test_webhook_dispatch_extended.py | 13 | P2 |
| test_language_detect.py | 8 | P2 |
| test_verification.py | 6 | P2 |
| test_chunker.py | 9 | P2 |
| test_dpgf_extractor.py | 10 | P2 |
| test_analyzer_orchestrator.py | 8 | P2 |
| test_analytics.py | 5 | P2 |
| test_boamp_watcher.py | 6 | P2 |
| test_cashflow_extended.py | 10 | P2 |
| test_gonogo_extended.py | 11 | P2 |
| test_e2e_pipeline.py | 4 | P0 |
| test_security.py | 15 | P0 |
| test_benchmarks.py | 10 | P3 |
| **TOTAL BACKEND** | **~261** | |

**Frontend (25 nouveaux fichiers)** :
| Fichier | Tests | Priorite |
|---------|-------|----------|
| CcapRiskTab.test.tsx | 7 | P0 |
| CctpAnalysisTab.test.tsx | 7 | P0 |
| RcAnalysisTab.test.tsx | 7 | P0 |
| AeAnalysisTab.test.tsx | 7 | P0 |
| ConflictsTab.test.tsx | 7 | P0 |
| DcCheckTab.test.tsx | 6 | P0 |
| QuestionsTab.test.tsx | 7 | P1 |
| ScoringSimulatorTab.test.tsx | 7 | P1 |
| DpgfPricingTab.test.tsx | 6 | P1 |
| SubcontractingTab.test.tsx | 7 | P1 |
| CashFlowTab.test.tsx | 6 | P1 |
| ProjectDetailPage.test.tsx | 7 | P0 |
| DashboardPage.test.tsx | 4 | P1 |
| PipelinePage.test.tsx | 4 | P2 |
| VeillePage.test.tsx | 5 | P2 |
| LibraryPage.test.tsx | 5 | P2 |
| BillingPage.test.tsx | 6 | P1 |
| SettingsCompanyPage.test.tsx | 4 | P2 |
| SettingsTeamPage.test.tsx | 4 | P2 |
| ErrorBoundary.test.tsx | 3 | P1 |
| api.test.ts | 6 | P0 |
| useProjects.test.ts | 6 | P1 |
| useAnalysis.test.ts | 5 | P1 |
| useDocuments.test.ts | 3 | P2 |
| useGlossary.test.ts | 2 | P2 |
| billing.store.test.ts | 4 | P2 |
| **TOTAL FRONTEND** | **~142** | |

### Total general : ~403 tests a creer + 85 existants = ~488 tests

### Ordre d'implementation recommande

**Sprint 1 (3 jours)** — P0 Backend :
- test_btp_pricing.py (32 tests, calculs critiques)
- test_security.py (15 tests)
- test_e2e_pipeline.py (4 tests)
- test_ccap/cctp/rc/ae_analyzer.py (32 tests)
- test_conflict_detector.py (11 tests)
- CI/CD coverage setup

**Sprint 2 (2 jours)** — P0 Frontend + P1 Backend :
- 6 onglets analyse (42 tests frontend)
- ProjectDetailPage + api.test.ts (13 tests frontend)
- test_dc_checker + test_retriever + test_llm_service (36 tests backend)

**Sprint 3 (2 jours)** — P1 :
- test_exporter + test_scoring + test_questions + test_subcontracting (35 tests)
- Frontend hooks + pages restantes (35 tests)

**Sprint 4 (1 jour)** — P2 + Performance :
- Services restants (40 tests)
- Benchmarks + Locust setup
