"""Référentiel CCAG-FCS 2021 — Fournitures Courantes et Services.

Encode les articles clés du CCAG applicable aux marchés de fournitures
courantes et de services (entretien, nettoyage, gardiennage, restauration,
maintenance…).

Source : Arrêté du 30 mars 2021 portant approbation du CCAG-FCS
(NOR: ECOM2104770A).
"""

from app.services.ccag_travaux_2021 import CcagArticle

CCAG_FCS_ARTICLES: list[CcagArticle] = [
    # --- AVANCE ---
    CcagArticle(
        article="10.1",
        title="Avance forfaitaire FCS",
        standard_value="5% du montant initial TTC si > 50 000 € HT et durée > 2 mois",
        numeric_value=5.0,
        unit="%",
        category="paiement",
        legal_source="CCAG-FCS 2021 art. 10.1 + art. R2191-3 CCP",
        alert_if_derogation=True,
    ),
    # --- RETENUE DE GARANTIE ---
    CcagArticle(
        article="10.3",
        title="Retenue de garantie FCS",
        standard_value="Plafonnée à 5% du montant initial TTC",
        numeric_value=5.0,
        unit="%",
        category="garanties",
        legal_source="CCAG-FCS 2021 art. 10.3",
        alert_if_derogation=True,
    ),
    # --- PÉNALITÉS DE RETARD LIVRAISON ---
    CcagArticle(
        article="15.1",
        title="Pénalités retard livraison FCS",
        standard_value="1/3000 du montant TTC des fournitures non livrées par jour calendaire",
        numeric_value=1 / 3000,
        unit="ratio/jour",
        category="penalites",
        legal_source="CCAG-FCS 2021 art. 15.1",
        alert_if_derogation=True,
    ),
    # --- DÉLAI DE PAIEMENT ---
    CcagArticle(
        article="12.1",
        title="Délai de paiement FCS",
        standard_value="30 jours à compter de la réception de la facture",
        numeric_value=30.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-FCS 2021 art. 12.1 + art. R2192-10 CCP",
        alert_if_derogation=True,
    ),
    # --- LIVRAISON ET RÉCEPTION ---
    CcagArticle(
        article="19.1",
        title="Vérification des fournitures",
        standard_value="Délai de vérification et admission : 30 jours après livraison",
        numeric_value=30.0,
        unit="jours",
        category="reception",
        legal_source="CCAG-FCS 2021 art. 19.1",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="19.3",
        title="Refus et remplacement FCS",
        standard_value="Fournitures non conformes refusées — remplacement dans délai fixé par l'acheteur",
        numeric_value=None,
        unit="obligation",
        category="reception",
        legal_source="CCAG-FCS 2021 art. 19.3",
        alert_if_derogation=False,
    ),
    # --- GARANTIE ---
    CcagArticle(
        article="20.1",
        title="Garantie des fournitures",
        standard_value="Garantie minimum 1 an à compter de la réception — vices cachés inclus",
        numeric_value=1.0,
        unit="an",
        category="garanties",
        legal_source="CCAG-FCS 2021 art. 20.1",
        alert_if_derogation=True,
    ),
    # --- SOUS-TRAITANCE ---
    CcagArticle(
        article="3.6",
        title="Sous-traitance FCS",
        standard_value="Autorisée avec accord de l'acheteur — titulaire reste responsable",
        numeric_value=None,
        unit="condition",
        category="sous-traitance",
        legal_source="CCAG-FCS 2021 art. 3.6 + art. L2193-1 CCP",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION ---
    CcagArticle(
        article="29.1",
        title="Résiliation pour faute FCS",
        standard_value="Résiliation aux frais et risques du titulaire après mise en demeure restée sans effet 8 jours",
        numeric_value=8.0,
        unit="jours",
        category="resiliation",
        legal_source="CCAG-FCS 2021 art. 29.1",
        alert_if_derogation=False,
    ),
    CcagArticle(
        article="29.3",
        title="Résiliation pour intérêt général FCS",
        standard_value="Indemnité = manque à gagner sur la part non exécutée + frais engagés",
        numeric_value=None,
        unit="indemnite",
        category="resiliation",
        legal_source="CCAG-FCS 2021 art. 29.3",
        alert_if_derogation=True,
    ),
    # --- PRIX ET RÉVISION ---
    CcagArticle(
        article="13.1",
        title="Prix ferme ou révisable FCS",
        standard_value="Prix ferme pour < 1 an — révisable obligatoire si durée > 1 an",
        numeric_value=1.0,
        unit="an",
        category="prix",
        legal_source="CCAG-FCS 2021 art. 13.1 + art. R2112-13 CCP",
        alert_if_derogation=True,
    ),
    # --- ASSURANCES ---
    CcagArticle(
        article="9.1",
        title="Assurances FCS",
        standard_value="RC exploitation et RC professionnelle — attestation avant démarrage",
        numeric_value=None,
        unit="obligation",
        category="assurances",
        legal_source="CCAG-FCS 2021 art. 9.1",
        alert_if_derogation=True,
    ),
    # --- NIVEAUX DE SERVICE ---
    CcagArticle(
        article="16.1",
        title="Niveaux de service FCS",
        standard_value="Le cahier des charges définit les niveaux de qualité — mesurables et vérifiables",
        numeric_value=None,
        unit="principe",
        category="qualite",
        legal_source="CCAG-FCS 2021 art. 16.1",
        alert_if_derogation=False,
    ),
]


def get_ccag_fcs_context() -> str:
    """Retourne un résumé des articles FCS pour injection dans les prompts."""
    lines = ["CCAG Fournitures Courantes et Services 2021 — Articles clés :"]
    for a in CCAG_FCS_ARTICLES:
        if a.alert_if_derogation:
            lines.append(f"• Art. {a.article} ({a.title}) : {a.standard_value}")
    return "\n".join(lines)
