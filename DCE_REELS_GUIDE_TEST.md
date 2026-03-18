# Guide de Test AO Copilot -- 5 DCE Reels + Protocole de Validation

> Date : 17 mars 2026
> Objectif : Tester les 17 analyseurs IA du SaaS AO Copilot sur des DCE reels et varies

---

## PARTIE 1 : Les 5 DCE identifies

---

### DCE #1 -- Commune de Chevremont -- VRD Contournement Place de l'Eglise

- **Type travaux :** VRD / Voirie / Terrassements / Espaces verts
- **Acheteur :** Commune de Chevremont (90, Territoire de Belfort)
- **Montant estime :** < 200 000 EUR HT (petit marche communal)
- **Nombre de lots :** 1 lot unique (Terrassements generaux - VRD - Espaces verts)
- **Procedure :** MAPA (procedure adaptee)
- **Statut :** Clos
- **Complexite :** Moyenne -- VRD pur, bon test pour le secteur Travaux Publics

**Documents disponibles et URLs :**

| Piece         | Disponible | URL |
|---------------|------------|-----|
| RC            | OUI        | http://www.chevremont.fr/IMG/pdf/RC_lot_VRD_TERRASSEMENT.pdf |
| CCTP          | OUI        | http://www.chevremont.fr/IMG/pdf/CHEVREMONT_-_CONTOURNEMENT_-_VRD_-_CCTP_-_DCE.pdf |
| DPGF          | OUI        | http://www.chevremont.fr/IMG/pdf/CONTOURNEMENT_DCE_VRD_DPGF_entreprise-3.pdf |
| AE            | OUI        | http://www.chevremont.fr/IMG/pdf/AE_LOT_VRD_TERRASSEMENT.pdf |
| CCAP          | PARTIEL    | References dans le CCTP (peut etre fusionne dans RC ou CCTP) |

**Documents bonus sur le meme site :**
- DPGF Cour primaire VRD : http://www.chevremont.fr/IMG/pdf/COUR_PRIMAIRE_DCE_DPGF_entreprise_VRD.pdf
- CCTP Cour elementaire : http://www.chevremont.fr/IMG/pdf/COUR_ELEMENTAIRE_CCTP_-_DCE.pdf
- CCTP Arret bus : http://www.chevremont.fr/IMG/pdf/ARRET_BUS_-_CCTP_-_DCE.pdf

**Pourquoi ce DCE :** Marche VRD communal typique. Test le secteur Travaux Publics (pas batiment). CCTP de 49 pages detaille. Contient RC + CCTP + DPGF + AE = 4 documents types. Ideal pour tester les analyseurs VRD, conflits intra-DCE, et pricing BTP.

---

### DCE #2 -- Ville de Pernes-les-Fontaines -- Rehabilitation Gare des Voyageurs et Lampisterie

- **Type travaux :** Rehabilitation batiment patrimonial (gare + lampisterie)
- **Acheteur :** Ville de Pernes-les-Fontaines (84210, Vaucluse)
- **Montant estime :** 300 000 - 600 000 EUR HT (rehabilitation multi-lots)
- **Nombre de lots :** 10 lots (tranche ferme lots 01 a 10)
- **Procedure :** MAPA (procedure adaptee, article 28 CMP)
- **Statut :** Clos (2013)
- **Complexite :** Elevee -- 10 lots, variante lot 7, PSE obligatoires

**Documents disponibles et URLs :**

| Piece         | Disponible | URL |
|---------------|------------|-----|
| DCE Complet (ZIP/PDF) | OUI | https://www.perneslesfontaines.fr/uploads/co_document/dce-gare-complet-1.pdf |
| DCE MOE       | OUI        | https://www.perneslesfontaines.fr/uploads/co_document/dce-complet-rehabilitation-gare-et-lampisterie.pdf |

Le PDF `dce-gare-complet-1.pdf` contient le DCE travaux complet avec :
- RC (Reglement de Consultation)
- CCAP (a accepter sans modification)
- CCTP par lot
- DPGF par lot
- AE

**Les 10 lots avec indices BT :**
- Lot 01 a Lot 10 (avec lot 07 = Electricite Chauffage VMC -- seul lot avec variante autorisee)

**Pourquoi ce DCE :** Cas complexe multi-lots ideal pour tester l'analyse multi-documents. 10 lots = test massif des analyseurs. Batiment patrimonial = contraintes specifiques. PSE obligatoires = test des conflits et checklist. DCE complet en un seul PDF = facilite le chargement.

---

### DCE #3 -- Commune du Boulou -- Rehabilitation Energetique Ecole Maternelle Jacques Prevert

- **Type travaux :** Renovation energetique batiment scolaire (ITE, chauffage, VMC)
- **Acheteur :** Commune du Boulou (66160, Pyrenees-Orientales)
- **Montant estime :** 400 000 - 800 000 EUR HT
- **Nombre de lots :** 10+ lots (gros oeuvre, ITE, serrurerie, echafaudages, chauffage/ventilation...)
- **Procedure :** MAPA (procedure adaptee ouverte, Code de la commande publique)
- **Statut :** Clos (2021-2022)
- **Complexite :** Elevee -- renovation energetique, reglementation thermique, multi-corps d'etat

**Documents disponibles et URLs :**

| Piece         | Disponible | URL |
|---------------|------------|-----|
| RC            | OUI        | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=17270&path=1_-_REGELEMENT_DE_LA_CONSULTATION.pdf |
| CCAP          | OUI        | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=93857&path=CCAP.pdf |
| CCTP+DPGF Lot 01 Gros Oeuvre | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61334&path=CCTP-DPGF-Lot-01-Gros-oeuvre.pdf |
| CCTP+DPGF Lot 06 ITE | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61342&path=CCTP-DPGF-Lot-06-Isolation-thermique-par-l-exterieur.pdf |
| CCTP+DPGF Lot 07 Serrurerie | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61338&path=CCTP-DPGF-Lot-07-Serrurerie.pdf |
| CCTP+DPGF Lot 08 Echafaudages | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61340&path=CCTP-DPGF-Lot-08-Echaffaudages.pdf |
| CCTP+DPGF Lot 10 Chauffage/VMC | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61346&path=CCTP-DPGF-Lot-10-Chauffage-Ventiflation.pdf |
| AE+CCAP+CCTP (doc combine) | OUI | https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=63220&path=AE-CCAP-CCTP-Annexe1-DPGF-AttestationVisite.pdf |
| Liste des avis | OUI | https://www.mairie-leboulou.fr/3637-liste-des-avis-d-appels-publics-a-la-concurrence.htm |

**Pourquoi ce DCE :** Renovation energetique = tendance forte 2025-2026 (fonds vert, RE2020). Multi-lots techniques (ITE, chauffage, VMC). CCTP+DPGF combines par lot = test de separation des documents. Reglementation thermique existant = test des references normatives. Ecole = contraintes specifiques (securite, accessibilite).

---

### DCE #4 -- Commune de Fontenay-le-Vicomte -- Travaux de Voirie Rue de la Mairie

- **Type travaux :** Voirie / Amenagement urbain (parvis mairie)
- **Acheteur :** Commune de Fontenay-le-Vicomte (91, Essonne)
- **Montant estime :** 50 000 - 150 000 EUR HT (contrat rural, petit marche)
- **Nombre de lots :** 1 lot unique
- **Procedure :** MAPA (marche a procedure adaptee)
- **Statut :** Clos
- **Complexite :** Simple -- bon cas de base pour un test initial

**Documents disponibles et URLs :**

| Piece         | Disponible | URL |
|---------------|------------|-----|
| DCE Complet (PDF unique) | OUI | https://www.fontenaylevicomte.fr/mod_turbolead/upload/file/COMMUNE%20DE%20FONTENAY%20LE%20VICOMTE%20CONTRAT%20RURAL%20-%20DCE%20VOIRIE%20RUE%20DE%20LA%20MAIRIE%20-%20VERSION%20PARVIS.pdf |

Le PDF unique contient RC + CCTP + DPGF fusionnes (format CCP typique des petits marches).

**Pourquoi ce DCE :** Cas basique ideal pour un premier test. Document unique fusionnant toutes les pieces. Petit marche communal de voirie = test du cas le plus simple. Permet de verifier que le systeme gere les CCP (CCAP+CCTP fusionnes).

---

### DCE #5 -- Ministere de la Culture -- Travaux de Creation de Vestiaires (5 lots)

- **Reference marche :** 2024-024-DBE
- **Type travaux :** Amenagement interieur (vestiaires) -- peinture, resine de sol, carrelage, menuiseries, travaux generaux
- **Acheteur :** Ministere de la Culture
- **Montant estime :** 100 000 - 300 000 EUR HT
- **Nombre de lots :** 5 lots
- **Procedure :** MAPA (via plateforme PLACE)
- **Statut :** Clos (2024)
- **Complexite :** Moyenne -- 5 lots second oeuvre, marche Etat

**Documents disponibles et URLs :**

| Piece         | Disponible | URL |
|---------------|------------|-----|
| RC            | OUI        | Via betterplace.info/files (fichier 2024_024_RC_TVX_vestiaires.pdf) |
| DCE Complet (ZIP) | OUI   | Via betterplace.info (fichier DCE.zip) |
| Page betterplace | OUI    | https://betterplace.info/dce/2582210 |
| Page PLACE originale | OUI | https://www.marches-publics.gouv.fr/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=2582210&orgAcronyme=f5j |

**Les 5 lots :**
- Lot 1 : Travaux generaux
- Lot 2 : Peinture
- Lot 3 : Resine de sol
- Lot 4 : Carrelage - Faience
- Lot 5 : Menuiseries interieure bois

**Pourquoi ce DCE :** Marche Etat (Ministere) = reference institutionnelle. Lots second oeuvre (peinture, carrelage) = test du cas basique PME BTP. 5 lots = complexite moderee. DCE ZIP complet disponible sur betterplace.info. Passage par PLACE = representatif des marches publics francais.

---

## PARTIE 2 : Sources complementaires de DCE

### Plateformes de marches publics (DCE telechargeables gratuitement)

| Plateforme | URL | Couverture |
|-----------|-----|-----------|
| PLACE (Etat) | https://www.marches-publics.gouv.fr/ | Marches de l'Etat et EPA |
| BOAMP | https://www.boamp.fr/ | Annonces officielles |
| e-marchespublics | https://www.e-marchespublics.com/ | Multi-acheteurs |
| Maximilien (IDF) | https://marches.maximilien.fr/ | Ile-de-France |
| Megalis Bretagne | https://marches.megalisbretagne.org/ | Bretagne |
| achatpublic.com | https://www.achatpublic.com/ | Multi-acheteurs |
| Klekoon | https://www.klekoon.com/ | Multi-acheteurs |
| Marchesonline | https://www.marchesonline.com/ | Agregateur (payant) |
| France Marches | https://www.francemarches.com/ | Agregateur |
| betterplace.info | https://betterplace.info/ | Transparence/archive DCE |

### Mots-cles de recherche par plateforme

Pour PLACE (marches-publics.gouv.fr) -- Recherche avancee :
- CPV 45000000 (Travaux de construction)
- CPV 45400000 (Travaux de parachèvement de batiment)
- CPV 45233000 (Travaux de construction de routes/voiries)
- Filtrer par "Consultations en cours" ou "Consultations cloturees"

Pour e-marchespublics.com :
- "travaux peinture" / "travaux plomberie" / "renovation ecole"
- "VRD voirie" / "isolation thermique" / "rehabilitation batiment"

Pour BOAMP :
- Code CPV + departement + type procedure

### Modeles et documents de reference (DAJ)

| Document | URL |
|---------|-----|
| CCAG-Travaux 2021 (tableau comparatif) | https://www.economie.gouv.fr/files/files/directions_services/daj/marches_publics/Consultation/2021.01.15_tableau_CCAG-Travaux%20VF.pdf |
| CCAP simplifie batiment (DAJ) | https://www.economie.gouv.fr/files/directions_services/daj/marches_publics/oeap/gem/ccap-s/ccap-s.pdf |
| Page CCAG et CCTG (DAJ) | https://www.economie.gouv.fr/daj/cahiers-clauses-administratives-generales-et-techniques |
| Modele marche MOE (Ordre des Architectes) | https://www.architectes.org/publications/modele-de-marche-public-de-maitrise-doeuvre-construction-neuve-et-rehabilitation |

---

## PARTIE 3 : Guide pas-a-pas pour telecharger un DCE

### Sur PLACE (marches-publics.gouv.fr)

1. Aller sur https://www.marches-publics.gouv.fr/
2. Menu "Recherche avancee" (ou lien direct : https://marches-publics.gouv.fr/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons=)
3. Renseigner les filtres :
   - Mot-cle : "travaux renovation" ou "VRD" ou "peinture"
   - Type : "Consultation"
   - Statut : "En cours" (ou "Cloturee" pour archivees)
4. Cliquer sur une consultation
5. Section "Telechargement du DCE" :
   - Telechargement anonyme : possible sans compte
   - Telechargement identifie : creer un compte gratuit (recommande pour etre notifie des modifications)
6. Telecharger le ZIP contenant RC, CCAP, CCTP, DPGF, AE, plans

### Sur e-marchespublics.com

1. Aller sur https://www.e-marchespublics.com/
2. Rechercher par mot-cle ou code CPV
3. Filtrer par departement, type de marche, date
4. Creer un compte gratuit
5. Acceder a la consultation et telecharger le DCE

### Sur betterplace.info (archive transparence)

1. Aller sur https://betterplace.info/
2. Rechercher par numero de consultation ou mot-cle
3. Les fichiers PDF et ZIP sont directement telechargeables
4. Format : betterplace.info/files/{id}-{fichier}.pdf ou betterplace.info/dce/{id}

---

## PARTIE 4 : Protocole de Validation -- Grille de Scoring

### 4.1 Matrice de test : 5 DCE x 17 analyseurs

| Analyseur | DCE #1 Chevremont VRD | DCE #2 Pernes Gare | DCE #3 Le Boulou Ecole | DCE #4 Fontenay Voirie | DCE #5 Culture Vestiaires |
|-----------|:-----:|:-----:|:-----:|:-----:|:-----:|
| 1. Resume (project_overview) | T | T | T | T | T |
| 2. Checklist conformite | T | T | T | T | T |
| 3. Criteres notation | T | T | T | T | T |
| 4. Risques CCAP | T | T | T | - | T |
| 5. Analyse RC | T | T | T | T | T |
| 6. Acte d'Engagement | T | - | T | - | T |
| 7. Analyse CCTP | T | T | T | T | T |
| 8. Verification admin (DC) | T | T | T | T | T |
| 9. Conflits intra-DCE | T | T | T | T | T |
| 10. Questions acheteur | T | T | T | T | T |
| 11. Scoring simulateur | T | T | T | T | T |
| 12. Pricing BTP | T | T | T | T | T |
| 13. Tresorerie/Cashflow | T | T | T | - | T |
| 14. Sous-traitance | T | T | T | - | T |
| 15. Calendrier/Delais | T | T | T | T | T |
| 16. Chat DCE (RAG) | T | T | T | T | T |
| 17. Export (PDF/Word) | T | T | T | T | T |

T = A tester | - = Non applicable (document absent)

### 4.2 Criteres de notation par analyseur (seuils Go/No-Go)

Pour chaque cellule de la matrice, noter sur 3 niveaux :

| Score | Signification | Critere |
|-------|--------------|---------|
| **PASS** (2 pts) | Resultat correct et exploitable | Pas de hallucination, donnees factuelles exactes, citations verifiables |
| **PARTIAL** (1 pt) | Resultat partiellement correct | Quelques erreurs mineures, mais globalement utilisable |
| **FAIL** (0 pt) | Resultat incorrect ou inutilisable | Hallucinations, donnees inventees, crash, timeout |

### 4.3 Seuils Go/No-Go

| Metrique | Seuil Go | Seuil No-Go |
|---------|----------|-------------|
| Score global (% PASS) | >= 75% | < 50% |
| Score Resume | 5/5 PASS | < 3/5 PASS |
| Score Checklist | 5/5 PASS | < 3/5 PASS |
| Score CCAP/CCTP | 4/5 PASS | < 3/5 PASS |
| Score Conflits | 4/5 PASS | < 2/5 PASS |
| Score Export | 5/5 PASS | < 4/5 PASS |
| Aucun FAIL critique | 0 FAIL sur Resume/Checklist | > 2 FAIL sur Resume/Checklist |
| Temps analyse moyen | < 120s par DCE | > 300s par DCE |
| Taux hallucination | 0% sur citations | > 10% hallucinations |

### 4.4 Grille de validation detaillee par DCE

Pour CHAQUE DCE, remplir ce tableau :

```
DCE #N : [Nom]
Date test : ____
Nombre docs uploades : ____
Temps total analyse : ____s
Score OCR moyen : ____%

| # | Analyseur | Score | Temps | Hallucinations | Citations OK | Notes |
|---|-----------|-------|-------|---------------|-------------|-------|
| 1 | Resume | _/2 | __s | Oui/Non | _/_ | |
| 2 | Checklist | _/2 | __s | Oui/Non | _/_ | |
| ... | ... | ... | ... | ... | ... | |

TOTAL : __/34 pts (___%)
Verdict : GO / NO-GO / A AMELIORER
```

### 4.5 Tests specifiques par type de DCE

**DCE #1 (VRD Chevremont) -- Tests cibles :**
- [ ] L'analyseur identifie correctement le type "VRD/Voirie" (pas "Batiment")
- [ ] Le CCTP de 49 pages est correctement decoupe en chunks
- [ ] Les references aux normes VRD (fascicule 70, DTU...) sont detectees
- [ ] La DPGF est correctement extraite avec les postes de prix
- [ ] Les conflits CCTP/DPGF sont detectes le cas echeant

**DCE #2 (Pernes Gare -- 10 lots) -- Tests cibles :**
- [ ] Les 10 lots sont correctement identifies et listes
- [ ] La variante lot 7 est signalee
- [ ] Les PSE obligatoires sont detectes dans la checklist
- [ ] Les indices BT par lot sont identifies
- [ ] Le CCAP est correctement separe du CCTP dans le PDF unique

**DCE #3 (Le Boulou Ecole -- Renovation energetique) -- Tests cibles :**
- [ ] La reglementation thermique (arrete du 3 mai 2007) est identifiee
- [ ] Les lots ITE et chauffage/VMC sont correctement analyses
- [ ] Le profil energetique est detecte dans le scoring
- [ ] Les normes RE2020 / RT existant sont referencees
- [ ] Les CCTP+DPGF combines sont correctement separes

**DCE #4 (Fontenay Voirie -- Cas simple) -- Tests cibles :**
- [ ] Le systeme gere un PDF unique (CCP fusionne)
- [ ] Le resume est pertinent malgre un document court
- [ ] Pas de sur-analyse (pas d'invention de lots inexistants)
- [ ] L'export PDF fonctionne meme avec peu de contenu

**DCE #5 (Culture Vestiaires -- 5 lots second oeuvre) -- Tests cibles :**
- [ ] Les 5 lots second oeuvre sont identifies
- [ ] Les prix de reference peinture/carrelage sont pertinents
- [ ] Le lot "resine de sol" (technique specifique) est correctement analyse
- [ ] La reference ministerielle est identifiee dans le resume

### 4.6 Checklist pre-test

Avant de lancer les tests :

- [ ] Backend API demarre et fonctionnel (`/api/health/ready`)
- [ ] Worker Celery actif et connecte a Redis
- [ ] PostgreSQL + pgvector operationnel
- [ ] Cle API Anthropic (Claude) configuree
- [ ] Cle API OpenAI (embeddings) configuree
- [ ] Espace disque suffisant (>1 Go)
- [ ] Les 5 DCE sont telecharges localement
- [ ] Compte utilisateur de test cree (plan Pro ou superieur)

### 4.7 Procedure de test

1. **Telecharger** les 5 DCE (PDFs) dans un dossier local
2. **Creer** 5 projets dans AO Copilot (un par DCE)
3. **Uploader** les documents de chaque DCE dans le projet correspondant
4. **Lancer l'analyse** sur chaque projet
5. **Parcourir** les 17 onglets pour chaque projet
6. **Remplir** la grille de scoring (4.4) pour chaque DCE
7. **Verifier** les citations (spot-check 3 citations par onglet)
8. **Tester** l'export PDF et Word pour chaque projet
9. **Calculer** le score global et appliquer les seuils Go/No-Go
10. **Documenter** les bugs, hallucinations et ameliorations necessaires

### 4.8 Rapport de test -- Template

```
# Rapport de Test AO Copilot -- DCE Reels
Date : ____
Version : ____
Testeur : ____

## Resume executif
- Score global : ___%
- Verdict : GO / NO-GO
- DCE testes : 5/5
- Analyseurs valides : __/17

## Scores par DCE
| DCE | Score | Verdict | Problemes |
|-----|-------|---------|-----------|
| #1 Chevremont VRD | __/34 | | |
| #2 Pernes Gare | __/34 | | |
| #3 Le Boulou Ecole | __/34 | | |
| #4 Fontenay Voirie | __/34 | | |
| #5 Culture Vestiaires | __/34 | | |

## Problemes critiques (FAIL)
1. ...
2. ...

## Ameliorations identifiees
1. ...
2. ...

## Annexes
- Screenshots des resultats
- Logs d'erreurs
- Fichiers DCE utilises
```

---

## PARTIE 5 : Commandes de telechargement

Script bash pour telecharger les DCE disponibles :

```bash
#!/bin/bash
# Telecharger les DCE reels pour test AO Copilot

mkdir -p test-dce-reels/{dce1-chevremont-vrd,dce2-pernes-gare,dce3-leboulou-ecole,dce4-fontenay-voirie,dce5-culture-vestiaires}

# DCE #1 - Chevremont VRD
curl -L -o "test-dce-reels/dce1-chevremont-vrd/RC_lot_VRD.pdf" \
  "http://www.chevremont.fr/IMG/pdf/RC_lot_VRD_TERRASSEMENT.pdf"
curl -L -o "test-dce-reels/dce1-chevremont-vrd/CCTP_VRD.pdf" \
  "http://www.chevremont.fr/IMG/pdf/CHEVREMONT_-_CONTOURNEMENT_-_VRD_-_CCTP_-_DCE.pdf"
curl -L -o "test-dce-reels/dce1-chevremont-vrd/DPGF_VRD.pdf" \
  "http://www.chevremont.fr/IMG/pdf/CONTOURNEMENT_DCE_VRD_DPGF_entreprise-3.pdf"
curl -L -o "test-dce-reels/dce1-chevremont-vrd/AE_VRD.pdf" \
  "http://www.chevremont.fr/IMG/pdf/AE_LOT_VRD_TERRASSEMENT.pdf"

# DCE #2 - Pernes-les-Fontaines Gare (DCE complet en 1 PDF)
curl -L -o "test-dce-reels/dce2-pernes-gare/DCE_COMPLET_GARE.pdf" \
  "https://www.perneslesfontaines.fr/uploads/co_document/dce-gare-complet-1.pdf"
curl -L -o "test-dce-reels/dce2-pernes-gare/DCE_MOE_GARE.pdf" \
  "https://www.perneslesfontaines.fr/uploads/co_document/dce-complet-rehabilitation-gare-et-lampisterie.pdf"

# DCE #3 - Le Boulou Ecole Maternelle (renovation energetique)
curl -L -o "test-dce-reels/dce3-leboulou-ecole/RC.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=17270&path=1_-_REGELEMENT_DE_LA_CONSULTATION.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCAP.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=93857&path=CCAP.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCTP_DPGF_Lot01_Gros_Oeuvre.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61334&path=CCTP-DPGF-Lot-01-Gros-oeuvre.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCTP_DPGF_Lot06_ITE.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61342&path=CCTP-DPGF-Lot-06-Isolation-thermique-par-l-exterieur.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCTP_DPGF_Lot07_Serrurerie.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61338&path=CCTP-DPGF-Lot-07-Serrurerie.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCTP_DPGF_Lot08_Echafaudages.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61340&path=CCTP-DPGF-Lot-08-Echaffaudages.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/CCTP_DPGF_Lot10_Chauffage_VMC.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=61346&path=CCTP-DPGF-Lot-10-Chauffage-Ventiflation.pdf"
curl -L -o "test-dce-reels/dce3-leboulou-ecole/AE_CCAP_CCTP_DPGF.pdf" \
  "https://www.mairie-leboulou.fr/cms_viewFile.php?idtf=63220&path=AE-CCAP-CCTP-Annexe1-DPGF-AttestationVisite.pdf"

# DCE #4 - Fontenay-le-Vicomte Voirie (PDF unique)
curl -L -o "test-dce-reels/dce4-fontenay-voirie/DCE_VOIRIE_COMPLET.pdf" \
  "https://www.fontenaylevicomte.fr/mod_turbolead/upload/file/COMMUNE%20DE%20FONTENAY%20LE%20VICOMTE%20CONTRAT%20RURAL%20-%20DCE%20VOIRIE%20RUE%20DE%20LA%20MAIRIE%20-%20VERSION%20PARVIS.pdf"

# DCE #5 - Ministere Culture Vestiaires (via betterplace)
curl -L -o "test-dce-reels/dce5-culture-vestiaires/RC.pdf" \
  "https://betterplace.info/files/2582210-reglement.pdf"
# Note: Le DCE complet est en ZIP, telecharger manuellement depuis :
# https://betterplace.info/dce/2582210

echo "Telechargement termine. Verifier les fichiers dans test-dce-reels/"
ls -la test-dce-reels/*/
```

---

## PARTIE 6 : Resume comparatif des 5 DCE

| # | DCE | Type | Montant | Lots | Docs | Difficulte test |
|---|-----|------|---------|------|------|----------------|
| 1 | Chevremont VRD | Voirie/VRD | <200K | 1 | RC+CCTP+DPGF+AE | Moyenne |
| 2 | Pernes Gare | Rehab. patrimoniale | 300-600K | 10 | DCE complet PDF | Haute |
| 3 | Le Boulou Ecole | Renov. energetique | 400-800K | 10+ | RC+CCAP+CCTP/DPGF*5+AE | Haute |
| 4 | Fontenay Voirie | Voirie simple | <150K | 1 | CCP unique | Basse |
| 5 | Culture Vestiaires | Second oeuvre | 100-300K | 5 | RC+DCE.zip | Moyenne |

**Couverture des criteres :**
- Petit chantier simple : DCE #4 (Fontenay)
- Rehabilitation batiment multi-lots : DCE #2 (Pernes, 10 lots)
- Construction/Renovation complexe : DCE #3 (Le Boulou, renovation energetique)
- VRD/Voirie : DCE #1 (Chevremont) + DCE #4 (Fontenay)
- Renovation energetique/thermique : DCE #3 (Le Boulou)
- Marche Etat : DCE #5 (Ministere de la Culture)
- Second oeuvre (peinture, carrelage) : DCE #5 (Culture)

---

*Document genere le 17 mars 2026 pour le projet AO Copilot*
