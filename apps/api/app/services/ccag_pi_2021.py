"""Référentiel CCAG-PI 2021 — Prestations Intellectuelles.

Encode les articles clés du CCAG applicable aux marchés de prestations
intellectuelles (études, maîtrise d'œuvre, AMO, expertise, conseil…).

Source : Arrêté du 30 mars 2021 portant approbation du CCAG-PI
(NOR: ECOM2104773A).
"""

from app.services.ccag_travaux_2021 import CcagArticle

CCAG_PI_ARTICLES: list[CcagArticle] = [
    # --- AVANCE ---
    CcagArticle(
        article="9.1",
        title="Avance forfaitaire PI",
        standard_value="5% du montant initial TTC si > 50 000 € HT et durée > 2 mois",
        numeric_value=5.0,
        unit="%",
        category="paiement",
        legal_source="CCAG-PI 2021 art. 9.1 + art. R2191-3 CCP",
        alert_if_derogation=True,
    ),
    # --- RETENUE DE GARANTIE ---
    CcagArticle(
        article="9.3",
        title="Retenue de garantie PI",
        standard_value="Plafonnée à 5% du montant initial TTC",
        numeric_value=5.0,
        unit="%",
        category="garanties",
        legal_source="CCAG-PI 2021 art. 9.3 + loi n° 71-584",
        alert_if_derogation=True,
    ),
    # --- PÉNALITÉS DE RETARD ---
    CcagArticle(
        article="14.1",
        title="Pénalités de retard PI",
        standard_value="1/3000 du montant TTC par jour calendaire de retard",
        numeric_value=1 / 3000,
        unit="ratio/jour",
        category="penalites",
        legal_source="CCAG-PI 2021 art. 14.1",
        alert_if_derogation=True,
    ),
    # --- DÉLAI DE PAIEMENT ---
    CcagArticle(
        article="11.1",
        title="Délai de paiement PI",
        standard_value="30 jours à compter de la réception de la demande de paiement",
        numeric_value=30.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-PI 2021 art. 11.1 + art. R2192-10 CCP",
        alert_if_derogation=True,
    ),
    # --- PROPRIÉTÉ INTELLECTUELLE ---
    CcagArticle(
        article="25.1",
        title="Cession des droits PI",
        standard_value="Le titulaire cède à l'acheteur les droits de propriété intellectuelle sur les livrables",
        numeric_value=None,
        unit="droit",
        category="propriete_intellectuelle",
        legal_source="CCAG-PI 2021 art. 25.1 + CPI art. L131-1",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="25.2",
        title="Droits réservés titulaire",
        standard_value="Utilisation antérieure du titulaire préservée — acheteur ne peut interdire l'usage des méthodes",
        numeric_value=None,
        unit="droit",
        category="propriete_intellectuelle",
        legal_source="CCAG-PI 2021 art. 25.2",
        alert_if_derogation=False,
    ),
    # --- CONFIDENTIALITÉ ---
    CcagArticle(
        article="5.1",
        title="Obligation de confidentialité PI",
        standard_value="Le titulaire est tenu à la confidentialité pendant toute la durée du marché et 5 ans après",
        numeric_value=5.0,
        unit="ans",
        category="confidentialite",
        legal_source="CCAG-PI 2021 art. 5.1",
        alert_if_derogation=False,
    ),
    # --- SOUS-TRAITANCE ---
    CcagArticle(
        article="3.6",
        title="Sous-traitance PI",
        standard_value="Autorisée avec accord préalable de l'acheteur — titulaire reste responsable",
        numeric_value=None,
        unit="condition",
        category="sous-traitance",
        legal_source="CCAG-PI 2021 art. 3.6 + art. L2193-1 CCP",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION ---
    CcagArticle(
        article="30.1",
        title="Résiliation pour faute PI",
        standard_value="Résiliation aux frais et risques du titulaire après mise en demeure restée sans effet 15 jours",
        numeric_value=15.0,
        unit="jours",
        category="resiliation",
        legal_source="CCAG-PI 2021 art. 30.1",
        alert_if_derogation=False,
    ),
    CcagArticle(
        article="30.3",
        title="Résiliation pour motif d'intérêt général PI",
        standard_value="Indemnité = manque à gagner + dépenses engagées et non amorties",
        numeric_value=None,
        unit="indemnite",
        category="resiliation",
        legal_source="CCAG-PI 2021 art. 30.3",
        alert_if_derogation=True,
    ),
    # --- VÉRIFICATION ET ADMISSION ---
    CcagArticle(
        article="26.1",
        title="Vérification des livrables PI",
        standard_value="Délai de vérification : 30 jours après remise du livrable",
        numeric_value=30.0,
        unit="jours",
        category="reception",
        legal_source="CCAG-PI 2021 art. 26.1",
        alert_if_derogation=True,
    ),
    CcagArticle(
        article="26.3",
        title="Admission tacite PI",
        standard_value="Absence de réponse dans les délais vaut admission du livrable",
        numeric_value=None,
        unit="principe",
        category="reception",
        legal_source="CCAG-PI 2021 art. 26.3",
        alert_if_derogation=True,
    ),
    # --- ASSURANCES ---
    CcagArticle(
        article="10.1",
        title="Assurance responsabilité civile PI",
        standard_value="RC professionnelle obligatoire — attestation à fournir avant démarrage",
        numeric_value=None,
        unit="obligation",
        category="assurances",
        legal_source="CCAG-PI 2021 art. 10.1",
        alert_if_derogation=True,
    ),
    # --- MODIFICATIONS ---
    CcagArticle(
        article="16.1",
        title="Modifications demandées par l'acheteur",
        standard_value="Toute modification fait l'objet d'un avenant ou d'un ordre de service — pas de modification unilatérale",
        numeric_value=None,
        unit="condition",
        category="modifications",
        legal_source="CCAG-PI 2021 art. 16.1",
        alert_if_derogation=True,
    ),
]


def get_ccag_pi_context() -> str:
    """Retourne un résumé des articles PI pour injection dans les prompts."""
    lines = ["CCAG Prestations Intellectuelles 2021 — Articles clés :"]
    for a in CCAG_PI_ARTICLES:
        if a.alert_if_derogation:
            lines.append(f"• Art. {a.article} ({a.title}) : {a.standard_value}")
    return "\n".join(lines)
