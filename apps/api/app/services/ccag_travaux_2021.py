"""Référentiel CCAG-Travaux 2021 (arrêté du 30 mars 2021).

Encode les articles clés du CCAG-Travaux pour permettre aux analyzers
(CCAP, AE, Conflits) de comparer les clauses d'un DCE au standard légal
et détecter les dérogations défavorables au titulaire.

Source : Arrêté du 30 mars 2021 portant approbation du cahier des clauses
administratives générales des marchés publics de travaux (NOR: ECOM2104772A).
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CcagArticle:
    """Un article de référence du CCAG-Travaux 2021."""

    article: str  # Ex: "14.1"
    title: str  # Titre court
    standard_value: str  # Valeur/règle standard en texte
    numeric_value: float | None  # Valeur numérique si applicable
    unit: str  # Unité (%, jours, €, ratio, etc.)
    category: str  # penalites | garanties | paiement | delais | resiliation | sous-traitance | assurances | reception
    legal_source: str  # Référence légale précise
    alert_if_derogation: bool  # True = signaler si le CCAP déroge


# ── Articles clés du CCAG-Travaux 2021 ────────────────────────────────────

CCAG_ARTICLES: list[CcagArticle] = [
    # --- AVANCE ---
    CcagArticle(
        article="14.1",
        title="Avance forfaitaire",
        standard_value="5% du montant initial TTC du marché (obligatoire si > 50 000 € HT et durée > 2 mois)",
        numeric_value=5.0,
        unit="%",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 14.1 + art. R2191-3 CCP",
        alert_if_derogation=True,
    ),
    # --- RETENUE DE GARANTIE ---
    CcagArticle(
        article="14.3",
        title="Retenue de garantie",
        standard_value="Plafonnée à 5% du montant initial TTC (substitution par caution possible)",
        numeric_value=5.0,
        unit="%",
        category="garanties",
        legal_source="CCAG-Travaux 2021 art. 14.3 + loi n° 71-584 du 16 juillet 1971",
        alert_if_derogation=True,
    ),
    # --- PÉNALITÉS DE RETARD ---
    CcagArticle(
        article="19.1",
        title="Pénalités de retard",
        standard_value="1/3000 du montant TTC du marché par jour calendaire de retard",
        numeric_value=1 / 3000,
        unit="ratio/jour",
        category="penalites",
        legal_source="CCAG-Travaux 2021 art. 19.1",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION ---
    CcagArticle(
        article="20.1",
        title="Indemnité de résiliation (faute MOA)",
        standard_value="5% du montant TTC des prestations non exécutées",
        numeric_value=5.0,
        unit="%",
        category="resiliation",
        legal_source="CCAG-Travaux 2021 art. 20.1 (résiliation pour motif d'intérêt général)",
        alert_if_derogation=True,
    ),
    # --- RÉVISION DE PRIX ---
    CcagArticle(
        article="10.1",
        title="Révision de prix",
        standard_value="Obligatoire si durée > 3 mois (sauf marché à prix ferme justifié)",
        numeric_value=3.0,
        unit="mois",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 10.1 + art. R2112-13 CCP",
        alert_if_derogation=True,
    ),
    # --- DÉLAI DE PAIEMENT ---
    CcagArticle(
        article="11.6",
        title="Délai de paiement",
        standard_value="30 jours à compter de la réception de la demande de paiement",
        numeric_value=30.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 11.6 + art. R2192-10 CCP",
        alert_if_derogation=True,
    ),
    # --- INTÉRÊTS MORATOIRES ---
    CcagArticle(
        article="11.7",
        title="Intérêts moratoires",
        standard_value="Taux BCE + 8 points (automatiques, sans mise en demeure)",
        numeric_value=8.0,
        unit="points au-dessus BCE",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 11.7 + décret n° 2013-269",
        alert_if_derogation=True,
    ),
    # --- RÉCEPTION ---
    CcagArticle(
        article="41.1",
        title="Délai de réception",
        standard_value="Le MOA dispose de 30 jours après demande pour prononcer la réception",
        numeric_value=30.0,
        unit="jours",
        category="reception",
        legal_source="CCAG-Travaux 2021 art. 41.1",
        alert_if_derogation=True,
    ),
    # --- SOUS-TRAITANCE ---
    CcagArticle(
        article="3.6",
        title="Sous-traitance",
        standard_value="Libre sous réserve d'acceptation et agrément des conditions de paiement par le MOA",
        numeric_value=None,
        unit="",
        category="sous-traitance",
        legal_source="CCAG-Travaux 2021 art. 3.6 + loi n° 75-1334 du 31 décembre 1975",
        alert_if_derogation=True,
    ),
    # --- ASSURANCES ---
    CcagArticle(
        article="9.1",
        title="Assurances obligatoires",
        standard_value="RC professionnelle + décennale (travaux soumis). Attestations sous 15 jours après notification",
        numeric_value=15.0,
        unit="jours",
        category="assurances",
        legal_source="CCAG-Travaux 2021 art. 9.1",
        alert_if_derogation=False,
    ),
    # --- FORCE MAJEURE ---
    CcagArticle(
        article="18.3",
        title="Force majeure",
        standard_value="Prolongation de délai pour événement imprévisible, irrésistible et extérieur",
        numeric_value=None,
        unit="",
        category="delais",
        legal_source="CCAG-Travaux 2021 art. 18.3 + art. 1218 Code civil",
        alert_if_derogation=True,
    ),
    # --- AJOURNEMENT ---
    CcagArticle(
        article="24.1",
        title="Ajournement des travaux",
        standard_value="Indemnisation si ajournement > 6 mois ou préjudice subi",
        numeric_value=6.0,
        unit="mois",
        category="delais",
        legal_source="CCAG-Travaux 2021 art. 24.1",
        alert_if_derogation=True,
    ),
    # --- GARANTIE DE PARFAIT ACHÈVEMENT ---
    CcagArticle(
        article="44.1",
        title="Garantie de parfait achèvement (GPA)",
        standard_value="1 an à compter de la date de réception",
        numeric_value=12.0,
        unit="mois",
        category="garanties",
        legal_source="CCAG-Travaux 2021 art. 44.1 + art. 1792-6 Code civil",
        alert_if_derogation=True,
    ),
    # --- GARANTIE BIENNALE ---
    CcagArticle(
        article="44.2",
        title="Garantie biennale (bon fonctionnement)",
        standard_value="2 ans pour les éléments d'équipement dissociables",
        numeric_value=24.0,
        unit="mois",
        category="garanties",
        legal_source="CCAG-Travaux 2021 art. 44.2 + art. 1792-3 Code civil",
        alert_if_derogation=False,
    ),
    # --- PRIX PROVISOIRES ---
    CcagArticle(
        article="10.3",
        title="Prix provisoires",
        standard_value="Doivent être convertis en prix définitifs dans un délai fixé par le marché",
        numeric_value=None,
        unit="",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 10.3",
        alert_if_derogation=False,
    ),
    # --- NANTISSEMENT ---
    CcagArticle(
        article="5.3",
        title="Nantissement / Cession de créances",
        standard_value="Le titulaire peut céder ou nantir les créances du marché (Dailly)",
        numeric_value=None,
        unit="",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 5.3 + art. L313-23 Code monétaire",
        alert_if_derogation=True,
    ),
    # --- PÉNALITÉS PLAFOND ---
    CcagArticle(
        article="19.2",
        title="Plafond des pénalités",
        standard_value="Pas de plafond par défaut dans le CCAG — à fixer dans le CCAP (usage : 5-10% du marché)",
        numeric_value=None,
        unit="%",
        category="penalites",
        legal_source="CCAG-Travaux 2021 art. 19.2 + jurisprudence",
        alert_if_derogation=True,
    ),

    # ── Articles ajoutés Phase 1 — Expansion couverture ────────────────────

    # --- ORDRE DE PRIORITÉ DES PIÈCES CONTRACTUELLES ---
    CcagArticle(
        article="3.1",
        title="Ordre de priorité des pièces contractuelles",
        standard_value="En cas de contradiction : CCAP > CCTP > AE et ses annexes > prix > CCAG (si non dérogé)",
        numeric_value=None,
        unit="",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 3.1",
        alert_if_derogation=True,
    ),
    # --- ATTACHEMENTS ET CONSTATATIONS ---
    CcagArticle(
        article="6.1",
        title="Attachements et constatations",
        standard_value="Le titulaire tient les attachements. Le MOE les vérifie contradictoirement. Silence 15j = acceptation",
        numeric_value=15.0,
        unit="jours",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 6.1",
        alert_if_derogation=False,
    ),
    # --- SOUS-TRAITANCE PAIEMENT DIRECT ---
    CcagArticle(
        article="8.1",
        title="Sous-traitance — paiement direct",
        standard_value="Paiement direct obligatoire si montant sous-traité > 600 € TTC",
        numeric_value=600.0,
        unit="€ TTC",
        category="sous-traitance",
        legal_source="CCAG-Travaux 2021 art. 8.1 + art. R2193-10 CCP",
        alert_if_derogation=True,
    ),
    # --- SITUATIONS MENSUELLES ---
    CcagArticle(
        article="12.1",
        title="Situations mensuelles des travaux",
        standard_value="Le titulaire remet mensuellement un projet de décompte au MOE. Silence 15j = accord tacite",
        numeric_value=15.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 12.1",
        alert_if_derogation=True,
    ),
    # --- SOLDE ET DÉCOMPTE GÉNÉRAL ---
    CcagArticle(
        article="13.1",
        title="Solde et décompte général",
        standard_value="Projet de décompte final dans 45 jours après réception. DGD par MOA dans 30 jours. Silence = acceptation",
        numeric_value=45.0,
        unit="jours",
        category="paiement",
        legal_source="CCAG-Travaux 2021 art. 13.1 à 13.4",
        alert_if_derogation=True,
    ),
    # --- AUGMENTATION MASSE DES TRAVAUX ---
    CcagArticle(
        article="15.2",
        title="Augmentation dans la masse des travaux",
        standard_value="Si augmentation > 5% du montant initial, le titulaire peut demander une indemnisation ou résiliation",
        numeric_value=5.0,
        unit="% du montant",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 15.2",
        alert_if_derogation=True,
    ),
    # --- DIMINUTION MASSE DES TRAVAUX ---
    CcagArticle(
        article="15.3",
        title="Diminution dans la masse des travaux",
        standard_value="Si diminution > 5% du montant initial, le titulaire peut être indemnisé pour le manque à gagner",
        numeric_value=5.0,
        unit="% du montant",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 15.3",
        alert_if_derogation=True,
    ),
    # --- CHANGEMENT NATURE OUVRAGES ---
    CcagArticle(
        article="16.1",
        title="Changement importance des natures d'ouvrages",
        standard_value="Si variation > 25% d'une nature d'ouvrage, le titulaire peut demander un nouveau prix unitaire",
        numeric_value=25.0,
        unit="%",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 16.1",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION DU FAIT DU TITULAIRE ---
    CcagArticle(
        article="20.2",
        title="Résiliation aux torts du titulaire",
        standard_value="Mise en demeure préalable. Excédent de coût des travaux restants à la charge du titulaire défaillant",
        numeric_value=None,
        unit="",
        category="resiliation",
        legal_source="CCAG-Travaux 2021 art. 20.2",
        alert_if_derogation=True,
    ),
    # --- RÉSILIATION POUR INTÉRÊT GÉNÉRAL ---
    CcagArticle(
        article="20.4",
        title="Résiliation pour motif d'intérêt général",
        standard_value="Le titulaire a droit à une indemnité de 5% des prestations non exécutées + dépenses engagées",
        numeric_value=5.0,
        unit="%",
        category="resiliation",
        legal_source="CCAG-Travaux 2021 art. 20.4",
        alert_if_derogation=True,
    ),
    # --- RÉCEPTION AVEC OU SANS RÉSERVES ---
    CcagArticle(
        article="21.1",
        title="Réception des travaux",
        standard_value="Prononcée avec ou sans réserves. Transfert de garde et des risques au maître d'ouvrage à la réception",
        numeric_value=None,
        unit="",
        category="reception",
        legal_source="CCAG-Travaux 2021 art. 21.1",
        alert_if_derogation=True,
    ),
    # --- MISE EN DEMEURE ---
    CcagArticle(
        article="22.1",
        title="Mise en demeure",
        standard_value="Délai minimum de 15 jours. Doit être notifiée par écrit avec objet et conséquences en cas de non-exécution",
        numeric_value=15.0,
        unit="jours",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 22.1",
        alert_if_derogation=True,
    ),
    # --- MESURES COERCITIVES ---
    CcagArticle(
        article="23.1",
        title="Mesures coercitives (exécution aux frais et risques)",
        standard_value="Après mise en demeure restée infructueuse. Les frais supplémentaires sont à la charge du titulaire défaillant",
        numeric_value=None,
        unit="",
        category="execution",
        legal_source="CCAG-Travaux 2021 art. 23.1",
        alert_if_derogation=True,
    ),
    # --- RESPONSABILITÉ VICES CACHÉS ---
    CcagArticle(
        article="45.1",
        title="Responsabilité — vices cachés et décennale",
        standard_value="Responsabilité décennale (10 ans) pour les ouvrages. Garantie dommages-ouvrage obligatoire pour le MOA",
        numeric_value=10.0,
        unit="ans",
        category="garanties",
        legal_source="CCAG-Travaux 2021 art. 45.1 + art. 1792 Code civil",
        alert_if_derogation=True,
    ),
    # --- RÈGLEMENT DES LITIGES ---
    CcagArticle(
        article="46",
        title="Règlement des litiges",
        standard_value="CCRA (Comité Consultatif de Règlement Amiable) avant saisine du tribunal administratif compétent",
        numeric_value=None,
        unit="",
        category="litiges",
        legal_source="CCAG-Travaux 2021 art. 46 + art. R2197-1 CCP",
        alert_if_derogation=True,
    ),
]


# ── Regroupements par analyseur ────────────────────────────────────────────

_CCAP_CATEGORIES = {
    "penalites", "garanties", "paiement", "delais",
    "resiliation", "sous-traitance", "assurances", "reception",
    "execution", "litiges",
}

_AE_CATEGORIES = {
    "penalites", "garanties", "paiement", "resiliation",
}

_CONFLICT_CATEGORIES = {
    "penalites", "garanties", "paiement", "delais",
    "resiliation", "sous-traitance", "execution",
}

_CCTP_CATEGORIES = {
    "garanties", "execution", "reception", "assurances",
}


def _format_articles_table(articles: list[CcagArticle]) -> str:
    """Formate les articles en table Markdown concise pour injection dans un prompt LLM."""
    lines = [
        "| Article | Titre | Standard CCAG | Source |",
        "|---------|-------|---------------|--------|",
    ]
    for a in articles:
        value = a.standard_value
        if a.numeric_value is not None and a.unit:
            value = f"{a.standard_value}"
        lines.append(
            f"| {a.article} | {a.title} | {value} | {a.legal_source} |"
        )
    return "\n".join(lines)


def get_ccag_context_for_analyzer(
    analyzer_type: Literal["ccap", "ae", "conflict", "cctp"],
) -> str:
    """Retourne le référentiel CCAG-Travaux 2021 formaté pour un type d'analyseur.

    Le texte retourné est injecté dans le system prompt de l'analyseur.
    Taille cible : < 1500 tokens (~6000 caractères).

    Args:
        analyzer_type: "ccap" pour l'analyseur CCAP, "ae" pour l'AE, "conflict" pour le détecteur de conflits.

    Returns:
        Texte formaté prêt à être injecté dans un prompt LLM.
    """
    category_map = {
        "ccap": _CCAP_CATEGORIES,
        "ae": _AE_CATEGORIES,
        "conflict": _CONFLICT_CATEGORIES,
        "cctp": _CCTP_CATEGORIES,
    }

    categories = category_map.get(analyzer_type, _CCAP_CATEGORIES)

    relevant = [
        a for a in CCAG_ARTICLES
        if a.category in categories and a.alert_if_derogation
    ]

    table = _format_articles_table(relevant)

    header = (
        "=== RÉFÉRENTIEL CCAG-TRAVAUX 2021 (arrêté du 30 mars 2021) ===\n\n"
        "Le tableau ci-dessous liste les standards du CCAG-Travaux 2021.\n"
        "Pour chaque clause du document analysé, COMPARE au standard CCAG.\n"
        "Si le document DÉROGE au CCAG de manière DÉFAVORABLE au titulaire, "
        "signale-le comme dérogation avec l'impact (DEFAVORABLE/FAVORABLE/NEUTRE).\n\n"
    )

    footer = (
        "\n\nRÈGLE IMPORTANTE : Une dérogation n'est pas forcément illégale. "
        "Le CCAP peut déroger au CCAG. Mais toute dérogation DÉFAVORABLE doit être signalée "
        "car elle représente un risque pour le titulaire du marché."
    )

    return header + table + footer


def get_ccag_article(article_num: str) -> CcagArticle | None:
    """Retourne un article CCAG par son numéro (ex: '14.1')."""
    for a in CCAG_ARTICLES:
        if a.article == article_num:
            return a
    return None


def get_ccag_articles_by_category(category: str) -> list[CcagArticle]:
    """Retourne tous les articles d'une catégorie donnée."""
    return [a for a in CCAG_ARTICLES if a.category == category]


# ═══════════════════════════════════════════════════════════════════════════════
# DÉROGATIONS CCAG COURANTES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CcagDerogation:
    """Dérogation CCAG courante avec évaluation juridique."""

    article_ccag: str          # "Art. 20.1"
    theme: str                 # "Pénalités"
    derogation_courante: str   # "Pénalités > 1/1000 du montant par jour"
    evaluation: str            # "Potentiellement abusif — jurisprudence CE 2019"
    risque: str                # "elevé" | "modéré" | "faible"


COMMON_DEROGATIONS: list[CcagDerogation] = [

    # --- PÉNALITÉS ---
    CcagDerogation(
        article_ccag="Art. 19.1",
        theme="Pénalités",
        derogation_courante="Pénalités de retard > 1/1000 du montant TTC par jour (au lieu de 1/3000 CCAG)",
        evaluation="Potentiellement abusif si montant cumulé disproportionné — CE, 14 mars 2022, Commune de Vitry-sur-Seine",
        risque="elevé",
    ),
    CcagDerogation(
        article_ccag="Art. 19.2",
        theme="Pénalités",
        derogation_courante="Absence de plafonnement des pénalités de retard (pas de plafond % du marché)",
        evaluation="Risque majeur — le juge peut moduler mais l'entreprise supporte le risque financier jusqu'au contentieux",
        risque="elevé",
    ),

    # --- DÉLAIS DE PAIEMENT ---
    CcagDerogation(
        article_ccag="Art. 11.6",
        theme="Délais de paiement",
        derogation_courante="Délai de paiement porté à 45 ou 60 jours (au lieu de 30 jours CCAG)",
        evaluation="Illégal pour les marchés publics — art. R2192-10 CCP impose 30 jours maximum. Clause réputée non écrite",
        risque="elevé",
    ),
    CcagDerogation(
        article_ccag="Art. 11.7",
        theme="Délais de paiement",
        derogation_courante="Intérêts moratoires à un taux inférieur au taux légal (BCE + 8 points)",
        evaluation="Illégal — le taux d'intérêts moratoires est fixé par décret, non dérogeable contractuellement",
        risque="elevé",
    ),

    # --- GARANTIES ---
    CcagDerogation(
        article_ccag="Art. 14.3",
        theme="Retenue de garantie",
        derogation_courante="Retenue de garantie supérieure à 5% du montant TTC",
        evaluation="Illégal — loi n° 71-584 du 16 juillet 1971 plafonne la retenue à 5%. Clause nulle",
        risque="elevé",
    ),
    CcagDerogation(
        article_ccag="Art. 44.1",
        theme="Garanties",
        derogation_courante="Extension de la GPA au-delà de 1 an (ex: 18 mois ou 2 ans)",
        evaluation="Légal mais défavorable — l'art. 1792-6 du Code civil fixe la GPA à 1 an. Une extension contractuelle est valide mais pénalisante",
        risque="modéré",
    ),

    # --- SOUS-TRAITANCE ---
    CcagDerogation(
        article_ccag="Art. 3.6",
        theme="Sous-traitance",
        derogation_courante="Interdiction totale de sous-traiter ou limitation à un pourcentage maximal (ex: 30%)",
        evaluation="Légalement discutable — la liberté de sous-traiter est un principe (loi 1975). Limitation possible si justifiée par l'objet du marché",
        risque="modéré",
    ),
    CcagDerogation(
        article_ccag="Art. 8.1",
        theme="Sous-traitance",
        derogation_courante="Suppression du paiement direct du sous-traitant ou conditions restrictives",
        evaluation="Illégal — le paiement direct est obligatoire dès que le montant sous-traité dépasse 600 € TTC (art. R2193-10 CCP)",
        risque="elevé",
    ),

    # --- RÉCEPTION ---
    CcagDerogation(
        article_ccag="Art. 41.1",
        theme="Réception",
        derogation_courante="Délai de réception porté à 60 ou 90 jours après demande du titulaire (au lieu de 30 jours CCAG)",
        evaluation="Défavorable au titulaire — retarde le démarrage des garanties et le solde. Acceptable si justifié par complexité technique",
        risque="modéré",
    ),
    CcagDerogation(
        article_ccag="Art. 21.1",
        theme="Réception",
        derogation_courante="Réception sous réserve de fourniture complète du DOE (blocage de la réception)",
        evaluation="Discutable — le DOE est exigible mais ne devrait pas bloquer la réception si l'ouvrage est utilisable. Risque de retenue abusive",
        risque="modéré",
    ),

    # --- RÉSILIATION ---
    CcagDerogation(
        article_ccag="Art. 20.1",
        theme="Résiliation",
        derogation_courante="Indemnité de résiliation pour intérêt général réduite à 2-3% (au lieu de 5% CCAG)",
        evaluation="Légal mais défavorable — le CE admet les clauses limitatives sauf déséquilibre significatif (CAA Lyon 2021)",
        risque="modéré",
    ),
    CcagDerogation(
        article_ccag="Art. 20.2",
        theme="Résiliation",
        derogation_courante="Résiliation pour faute sans mise en demeure préalable ou avec délai réduit (< 15 jours)",
        evaluation="Irrégulier — la mise en demeure est une formalité substantielle (CE, 8 oct. 2014, n° 370644). Clause contestable",
        risque="elevé",
    ),

    # --- ASSURANCES ---
    CcagDerogation(
        article_ccag="Art. 9.1",
        theme="Assurances",
        derogation_courante="Exigence d'assurances complémentaires (tous risques chantier, perte de recettes) au-delà du CCAG",
        evaluation="Légal si proportionné à l'objet du marché. Vérifier que les montants de couverture ne sont pas disproportionnés",
        risque="modéré",
    ),

    # --- PRIX / RÉVISION ---
    CcagDerogation(
        article_ccag="Art. 10.1",
        theme="Prix",
        derogation_courante="Prix ferme pour un marché de durée > 3 mois sans justification",
        evaluation="Illégal — art. R2112-13 CCP impose une révision de prix pour les marchés > 3 mois sauf justification exceptionnelle",
        risque="elevé",
    ),

    # --- AVANCE FORFAITAIRE ---
    CcagDerogation(
        article_ccag="Art. 14.1",
        theme="Avance forfaitaire",
        derogation_courante="Suppression ou réduction de l'avance forfaitaire (< 5%) pour un marché > 50 000 € HT",
        evaluation="Illégal — l'avance est obligatoire à 5% minimum pour les marchés > 50 000 € HT et durée > 2 mois (art. R2191-3 CCP)",
        risque="elevé",
    ),
]


def get_common_derogations() -> list[dict]:
    """Retourne les dérogations CCAG courantes sous forme de dictionnaires.

    Returns:
        Liste de dicts avec article_ccag, theme, derogation_courante,
        evaluation et risque.
    """
    return [
        {
            "article_ccag": d.article_ccag,
            "theme": d.theme,
            "derogation_courante": d.derogation_courante,
            "evaluation": d.evaluation,
            "risque": d.risque,
        }
        for d in COMMON_DEROGATIONS
    ]
