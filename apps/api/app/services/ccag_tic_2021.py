"""Référentiel CCAG-TIC 2021 — Technologies de l'Information et de la Communication.

Encode les articles clés du CCAG applicable aux marchés de TIC
(développement logiciel, infrastructure IT, hébergement, cybersécurité,
intégration de systèmes…).

Source : Arrêté du 30 mars 2021 portant approbation du CCAG-TIC
(NOR: ECOM2104771A).
"""

from app.services.ccag_travaux_2021 import CcagArticle

CCAG_TIC_ARTICLES: list[CcagArticle] = [
    # --- AVANCE ---
    CcagArticle(
        article="10.1",
        title="Avance forfaitaire TIC",
        standard_value="5% du montant initial TTC si > 50 000 € HT et durée > 2 mois",
        numeric_value=5.0,
        unit="%",
        category="paiement",
        legal_source="CCAG-TIC 2021 art. 10.1 + art. R2191-3 CCP",
        alert_if_derogation=True,
    ),
    # --- RETENUE DE GARANTIE ---
    CcagArticle(
        article="10.3",
        title="Retenue de garantie TIC",
        standard_value="Plafonnée à 5% du montant initial TTC",
        numeric_value=5.0,
        unit="%",
        category="garanties",
        legal_source="CCAG-TIC 2021 art. 10.3",
        alert_if_derogation=True,
    ),
    # --- PÉNALITÉS ---
    CcagArticle(
        article="14.1",
        title="Pénalités de retard TIC",
        standard_value="1/3000 du montant TTC du marché par jour calendaire de retard",
        numeric_value=1 / 3000,
        unit="ratio/jour",
        category="penalites",
        legal_source="CCAG-TIC 2021 art. 14.1",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="14.2",
        title="Pénalités de non-performance TIC",
        standard_value="Pénalités applicables si les niveaux de service (SLA) ne sont pas atteints",
        numeric_value=None,
        unit="SLA",
        category="penalites",
        legal_source="CCAG-TIC 2021 art. 14.2",
        alert_if_derogation=True,
    ),
    # --- DÉLAI DE PAIEMENT ---
    CcagArticle(
        article="12.1",
        title="Délai de paiement TIC",
        standard_value="30 jours à compter de la réception de la demande de paiement",
        numeric_value=30.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-TIC 2021 art. 12.1 + art. R2192-10 CCP",
        alert_if_derogation=True,
    ),
    # --- PROPRIÉTÉ DES DÉVELOPPEMENTS ---
    CcagArticle(
        article="24.1",
        title="Propriété des logiciels développés",
        standard_value="Les développements spécifiques appartiennent à l'acheteur — droits cédés en exclusivité",
        numeric_value=None,
        unit="droit",
        category="propriete_intellectuelle",
        legal_source="CCAG-TIC 2021 art. 24.1 + CPI art. L121-7",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="24.3",
        title="Code source TIC",
        standard_value="Code source livré avec la documentation technique — acheteur peut l'utiliser librement",
        numeric_value=None,
        unit="livrable",
        category="propriete_intellectuelle",
        legal_source="CCAG-TIC 2021 art. 24.3",
        alert_if_derogation=True,
    ),
    # --- RÉVERSIBILITÉ ---
    CcagArticle(
        article="26.1",
        title="Réversibilité et portabilité",
        standard_value="Obligation de réversibilité en fin de marché — données exportées dans format standard",
        numeric_value=None,
        unit="obligation",
        category="reversibilite",
        legal_source="CCAG-TIC 2021 art. 26.1",
        alert_if_derogation=True,
    ),
    # --- SÉCURITÉ ---
    CcagArticle(
        article="5.1",
        title="Sécurité des systèmes TIC",
        standard_value="Obligation de sécurité des données et des systèmes — conformité RGPD",
        numeric_value=None,
        unit="obligation",
        category="securite",
        legal_source="CCAG-TIC 2021 art. 5.1 + RGPD art. 28",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="5.2",
        title="Notification des incidents TIC",
        standard_value="Notification à l'acheteur sous 72h en cas d'incident de sécurité ou violation de données",
        numeric_value=72.0,
        unit="heures",
        category="securite",
        legal_source="CCAG-TIC 2021 art. 5.2 + RGPD art. 33",
        alert_if_derogation=True,
    ),
    # --- RECETTE ---
    CcagArticle(
        article="21.1",
        title="Recette des prestations TIC",
        standard_value="Phase de recette : 30 jours après livraison — cahier de tests obligatoire",
        numeric_value=30.0,
        unit="jours",
        category="reception",
        legal_source="CCAG-TIC 2021 art. 21.1",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="21.3",
        title="Recette provisoire et définitive TIC",
        standard_value="Recette provisoire puis définitive après période de garantie — 1 an minimum",
        numeric_value=1.0,
        unit="an",
        category="reception",
        legal_source="CCAG-TIC 2021 art. 21.3",
        alert_if_derogation=True,
    ),
    # --- SOUS-TRAITANCE ---
    CcagArticle(
        article="3.6",
        title="Sous-traitance TIC",
        standard_value="Autorisée avec accord de l'acheteur — titulaire reste responsable",
        numeric_value=None,
        unit="condition",
        category="sous-traitance",
        legal_source="CCAG-TIC 2021 art. 3.6 + art. L2193-1 CCP",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION ---
    CcagArticle(
        article="28.1",
        title="Résiliation pour faute TIC",
        standard_value="Résiliation aux frais et risques après mise en demeure sans effet 15 jours",
        numeric_value=15.0,
        unit="jours",
        category="resiliation",
        legal_source="CCAG-TIC 2021 art. 28.1",
        alert_if_derogation=False,
    ),
    CcagArticle(
        article="28.3",
        title="Résiliation intérêt général TIC",
        standard_value="Indemnité = manque à gagner sur part non exécutée + investissements amortissables",
        numeric_value=None,
        unit="indemnite",
        category="resiliation",
        legal_source="CCAG-TIC 2021 art. 28.3",
        alert_if_derogation=True,
    ),
    # --- CONTINUITÉ DE SERVICE ---
    CcagArticle(
        article="17.1",
        title="Continuité de service TIC",
        standard_value="Plan de continuité obligatoire — RTO et RPO définis dans le CCTP",
        numeric_value=None,
        unit="SLA",
        category="qualite",
        legal_source="CCAG-TIC 2021 art. 17.1",
        alert_if_derogation=False,
    ),
]


def get_ccag_tic_context() -> str:
    """Retourne un résumé des articles TIC pour injection dans les prompts."""
    lines = ["CCAG Technologies de l'Information et de la Communication 2021 — Articles clés :"]
    for a in CCAG_TIC_ARTICLES:
        if a.alert_if_derogation:
            lines.append(f"• Art. {a.article} ({a.title}) : {a.standard_value}")
    return "\n".join(lines)
