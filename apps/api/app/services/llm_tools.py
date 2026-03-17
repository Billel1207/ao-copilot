"""Outils Claude Tool Use — vérification références juridiques BTP.

3 outils que Claude peut appeler pendant l'analyse pour vérifier :
1. Articles CCAG-Travaux 2021 (contenu exact)
2. Seuils légaux (avance, paiement direct, pénalités)
3. Calcul de pénalités

Utilisé par llm_service.complete_json_with_tools() dans ccap_analyzer
et conflict_detector.
"""

# ── Tool definitions (Anthropic format) ──────────────────────────────

LEGAL_TOOLS = [
    {
        "name": "check_ccag_article",
        "description": (
            "Vérifie le contenu exact d'un article du CCAG-Travaux 2021. "
            "Utile pour confirmer un numéro d'article, sa valeur standard et ses conditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "article_number": {
                    "type": "string",
                    "description": "Numéro de l'article CCAG (ex: '14.1', '20.1', '41.3')",
                },
            },
            "required": ["article_number"],
        },
    },
    {
        "name": "check_legal_threshold",
        "description": (
            "Vérifie un seuil légal du Code de la Commande Publique 2019. "
            "Types: avance, paiement_direct, retenue_garantie, delai_paiement, "
            "sous_traitance, penalites, garantie_premiere_demande."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_type": {
                    "type": "string",
                    "description": "Type de seuil à vérifier",
                    "enum": [
                        "avance",
                        "paiement_direct",
                        "retenue_garantie",
                        "delai_paiement",
                        "sous_traitance",
                        "penalites",
                        "garantie_premiere_demande",
                    ],
                },
            },
            "required": ["threshold_type"],
        },
    },
    {
        "name": "compute_penalty",
        "description": (
            "Calcule le montant des pénalités de retard selon la formule CCAG. "
            "Formule standard : 1/1000e du montant HT par jour calendaire."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "montant_marche_ht": {
                    "type": "number",
                    "description": "Montant HT du marché en euros",
                },
                "nb_jours_retard": {
                    "type": "integer",
                    "description": "Nombre de jours calendaires de retard",
                },
                "taux_par_jour": {
                    "type": "number",
                    "description": "Taux par jour (défaut: 1/1000 = 0.001)",
                    "default": 0.001,
                },
                "plafond_percent": {
                    "type": "number",
                    "description": "Plafond en % du montant (défaut: 10%)",
                    "default": 10.0,
                },
            },
            "required": ["montant_marche_ht", "nb_jours_retard"],
        },
    },
]


# ── Tool handlers ────────────────────────────────────────────────────

# Legal thresholds from Code de la Commande Publique 2019
_LEGAL_THRESHOLDS = {
    "avance": (
        "Avance forfaitaire (art. R2191-3 à R2191-12 CCP) :\n"
        "- Obligatoire si marché > 50 000 € HT et durée > 2 mois\n"
        "- Montant : 5% du montant initial TTC (20% pour PME si demandé)\n"
        "- Remboursement : débute quand les sommes dues atteignent 65% du montant du marché\n"
        "- Remboursement terminé quand 80% atteint\n"
        "- Peut être portée à 60% avec garantie à première demande"
    ),
    "paiement_direct": (
        "Paiement direct des sous-traitants (art. L2193-10 à L2193-14 CCP) :\n"
        "- Obligatoire dès que le montant du sous-traité dépasse 600 € TTC\n"
        "- Le titulaire doit déclarer ses sous-traitants au pouvoir adjudicateur\n"
        "- Le sous-traitant adresse sa demande de paiement au titulaire\n"
        "- Délai de paiement : identique au marché principal (30 jours)"
    ),
    "retenue_garantie": (
        "Retenue de garantie (art. R2191-32 à R2191-35 CCP) :\n"
        "- Maximum : 5% du montant initial du marché (augmenté des avenants)\n"
        "- Peut être remplacée par une garantie à première demande\n"
        "- Libérée un mois après l'expiration du délai de garantie de parfait achèvement\n"
        "- Délai de garantie : 1 an à compter de la réception (art. 44.1 CCAG)"
    ),
    "delai_paiement": (
        "Délai de paiement (art. R2192-10 à R2192-12 CCP) :\n"
        "- État : 30 jours\n"
        "- Collectivités territoriales : 30 jours\n"
        "- Établissements de santé : 50 jours\n"
        "- Intérêts moratoires automatiques si dépassement\n"
        "- Taux = taux BCE + 8 points"
    ),
    "sous_traitance": (
        "Sous-traitance (art. L2193-1 à L2193-14 CCP, loi 75-1334) :\n"
        "- Autorisée sauf interdiction explicite dans le RC\n"
        "- Déclaration obligatoire au pouvoir adjudicateur (DC4)\n"
        "- Pas de sous-traitance totale du marché (jurisprudence)\n"
        "- Paiement direct obligatoire > 600 € TTC\n"
        "- Le titulaire reste responsable de l'exécution"
    ),
    "penalites": (
        "Pénalités de retard (art. 20.1 CCAG-Travaux 2021) :\n"
        "- Taux standard : 1/1000e du montant HT par jour calendaire\n"
        "- Applicables sans mise en demeure préalable\n"
        "- Non plafonnées par le CCAG (mais peuvent l'être dans le CCAP)\n"
        "- Déduites des acomptes ou du solde\n"
        "- Exonération si retard dû à un événement de force majeure"
    ),
    "garantie_premiere_demande": (
        "Garantie à première demande (art. R2191-36 CCP) :\n"
        "- Peut se substituer à la retenue de garantie\n"
        "- Émise par un établissement financier\n"
        "- Le pouvoir adjudicateur ne peut la refuser\n"
        "- Libérée dans les mêmes conditions que la retenue de garantie\n"
        "- Montant : identique à la retenue de garantie (max 5%)"
    ),
}


def handle_legal_tool(tool_name: str, tool_input: dict) -> str:
    """Handle a tool call from Claude during analysis."""

    if tool_name == "check_ccag_article":
        return _check_ccag_article(tool_input.get("article_number", ""))

    elif tool_name == "check_legal_threshold":
        threshold_type = tool_input.get("threshold_type", "")
        return _LEGAL_THRESHOLDS.get(
            threshold_type,
            f"Seuil '{threshold_type}' non trouvé. Types disponibles : {', '.join(_LEGAL_THRESHOLDS.keys())}",
        )

    elif tool_name == "compute_penalty":
        return _compute_penalty(
            montant_ht=tool_input.get("montant_marche_ht", 0),
            nb_jours=tool_input.get("nb_jours_retard", 0),
            taux=tool_input.get("taux_par_jour", 0.001),
            plafond_pct=tool_input.get("plafond_percent", 10.0),
        )

    return f"Outil '{tool_name}' inconnu."


def _check_ccag_article(article_number: str) -> str:
    """Look up a CCAG-Travaux 2021 article by number."""
    try:
        from app.services.ccag_travaux_2021 import CCAG_ARTICLES

        # Normalize: "14.1" or "article 14.1"
        num = article_number.lower().replace("article", "").strip()

        for a in CCAG_ARTICLES:
            if a.article == num:
                return (
                    f"Article {a.article} — {a.title}\n"
                    f"Valeur standard : {a.standard_value}\n"
                    f"Catégorie : {a.category}\n"
                    f"Source légale : {a.legal_source}\n"
                    f"Alerte dérogation : {'Oui' if a.alert_if_derogation else 'Non'}"
                )

        # Try partial match
        matches = [a for a in CCAG_ARTICLES if a.article.startswith(num.split(".")[0])]
        if matches:
            listing = "\n".join(f"  - Art. {a.article}: {a.title}" for a in matches[:5])
            return f"Article '{num}' exact non trouvé. Articles proches :\n{listing}"

        return f"Article '{num}' non trouvé dans les {len(CCAG_ARTICLES)} articles CCAG-Travaux 2021."

    except ImportError:
        return "Module CCAG non disponible."


def _compute_penalty(montant_ht: float, nb_jours: int, taux: float, plafond_pct: float) -> str:
    """Compute delay penalties."""
    penalite_brute = montant_ht * taux * nb_jours
    plafond = montant_ht * plafond_pct / 100
    penalite_finale = min(penalite_brute, plafond)

    return (
        f"Calcul pénalités de retard :\n"
        f"- Montant marché HT : {montant_ht:,.2f} €\n"
        f"- Retard : {nb_jours} jours calendaires\n"
        f"- Taux : {taux} par jour ({taux*100:.2f}%)\n"
        f"- Pénalité brute : {penalite_brute:,.2f} €\n"
        f"- Plafond ({plafond_pct}%) : {plafond:,.2f} €\n"
        f"- Pénalité finale : {penalite_finale:,.2f} €\n"
        f"{'⚠ PLAFOND ATTEINT' if penalite_brute >= plafond else ''}"
    )
