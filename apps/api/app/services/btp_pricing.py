"""Référentiel de prix BTP + analyse des postes DPGF + indices INSEE.

Module statique de référence prix (aucun appel LLM). Contient un dictionnaire
de 60+ types de postes BTP courants avec fourchettes de prix indicatifs
2024 France métropolitaine, ajustés 2026 via coefficient (+8%).

⚠️  AVERTISSEMENT : Les prix sont des FOURCHETTES INDICATIVES établies à partir
de moyennes constatées sur marchés publics attribués, indices BT/TP publics
(INSEE), et publications professionnelles (FFB, FNTP). Ils ne constituent PAS
des prix contractuels. Les écarts régionaux, la conjoncture matériaux et la
complexité du chantier peuvent faire varier les prix de ±30%.

Fonctions principales :
- check_dpgf_pricing() : compare les lignes DPGF au référentiel et signale
  les postes sous-évalués, surévalués ou normaux.
- get_pricing_reference() : recherche dans le référentiel par mot-clé.
- apply_price_adjustment() : calcule un prix ajusté avec un indice BT/TP.
- detect_revision_formula() : détecte la formule de révision dans un texte AE/CCAP.
"""
from __future__ import annotations

import structlog
import re
from dataclasses import dataclass
from typing import Any

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COEFFICIENT D'AJUSTEMENT 2026
# Inflation matériaux + MO constatée entre base 2024 et mars 2026.
# Source : évolution indices BT01 et TP01 (INSEE) sur la période.
# ═══════════════════════════════════════════════════════════════════════════════

PRICE_ADJUSTMENT_2026: float = 1.08  # +8% depuis base prix 2024


# ═══════════════════════════════════════════════════════════════════════════════
# INDICES DE PRIX BTP — INSEE (BT/TP)
# Utilisés pour la révision de prix des marchés publics.
# Formule type : P = P0 × [0.15 + 0.85 × (BT01n / BT01_0)]
# Réf : art. R2112-13 du CCP + CCAG-Travaux 2021 Art. 10
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PriceIndexTemplate:
    """Indice de prix BTP pour la révision des marchés."""
    code: str           # "BT01", "TP01", "TP02", "TP10a"
    nom: str            # Nom complet
    description: str    # Description courte
    base_value: float   # Valeur de base (janv. 2024)
    latest_value: float # Dernière valeur connue
    latest_date: str    # Date de la dernière valeur
    part_fixe: float    # Part fixe typique (0.15)
    part_variable: float  # Part variable (0.85)
    keywords: tuple[str, ...]  # Pour détection automatique


PRICE_INDEXES: list[PriceIndexTemplate] = [
    PriceIndexTemplate(
        code="BT01",
        nom="Index Bâtiment tous corps d'état",
        description="Indice global bâtiment — utilisé pour les marchés de construction tous corps d'état",
        base_value=118.2,
        latest_value=127.7,
        latest_date="2025-12",
        part_fixe=0.15,
        part_variable=0.85,
        keywords=("bâtiment", "construction", "tous corps", "tce", "bt01"),
    ),
    PriceIndexTemplate(
        code="TP01",
        nom="Index Travaux Publics — Tous travaux",
        description="Indice global travaux publics — VRD, génie civil, ouvrages d'art",
        base_value=112.5,
        latest_value=121.5,
        latest_date="2025-12",
        part_fixe=0.15,
        part_variable=0.85,
        keywords=("travaux publics", "vrd", "génie civil", "tp01", "infrastructure"),
    ),
    PriceIndexTemplate(
        code="TP02",
        nom="Index Travaux Publics — Terrassements",
        description="Indice spécifique terrassements généraux et fondations spéciales",
        base_value=113.8,
        latest_value=122.9,
        latest_date="2025-12",
        part_fixe=0.15,
        part_variable=0.85,
        keywords=("terrassement", "fondation", "excavation", "tp02"),
    ),
    PriceIndexTemplate(
        code="TP10a",
        nom="Index Travaux Publics — Canalisations, adductions d'eau",
        description="Indice canalisations eau potable et assainissement",
        base_value=110.4,
        latest_value=119.2,
        latest_date="2025-12",
        part_fixe=0.15,
        part_variable=0.85,
        keywords=("canalisation", "eau", "assainissement", "adduction", "tp10"),
    ),
    PriceIndexTemplate(
        code="TP09",
        nom="Index Travaux Publics — Électricité, courants faibles",
        description="Indice travaux électriques, éclairage public, courants faibles",
        base_value=108.9,
        latest_value=117.6,
        latest_date="2025-12",
        part_fixe=0.15,
        part_variable=0.85,
        keywords=("électricité", "éclairage", "courant", "tp09"),
    ),
]

# Index par code pour accès rapide
_INDEX_BY_CODE: dict[str, PriceIndexTemplate] = {idx.code: idx for idx in PRICE_INDEXES}


def get_price_index(code: str) -> PriceIndexTemplate | None:
    """Retourne un indice de prix par son code."""
    return _INDEX_BY_CODE.get(code.upper())


def apply_price_adjustment(
    prix_base: float,
    index_code: str = "BT01",
    base_date: str = "2024-01",
) -> dict[str, Any]:
    """Calcule le prix ajusté avec l'indice de révision spécifié.

    Formule : P = P0 × [part_fixe + part_variable × (Index_n / Index_0)]

    Args:
        prix_base: Prix de base HT.
        index_code: Code de l'indice (BT01, TP01, etc.).
        base_date: Date de base du prix (mois-0 du marché).

    Returns:
        Dict avec prix_base, prix_ajuste, coefficient, index_code, formule.
    """
    idx = _INDEX_BY_CODE.get(index_code.upper())
    if not idx:
        return {
            "prix_base": prix_base,
            "prix_ajuste": prix_base,
            "coefficient": 1.0,
            "index_code": index_code,
            "erreur": f"Indice {index_code} non trouvé",
        }

    coefficient = idx.part_fixe + idx.part_variable * (idx.latest_value / idx.base_value)
    prix_ajuste = round(prix_base * coefficient, 2)

    return {
        "prix_base": prix_base,
        "prix_ajuste": prix_ajuste,
        "coefficient": round(coefficient, 4),
        "index_code": idx.code,
        "index_nom": idx.nom,
        "index_base": idx.base_value,
        "index_latest": idx.latest_value,
        "index_date": idx.latest_date,
        "formule": f"P = {prix_base:.2f} × [{idx.part_fixe} + {idx.part_variable} × ({idx.latest_value}/{idx.base_value})]",
    }


def detect_revision_formula(text: str) -> dict | None:
    """Détecte une formule de révision de prix dans un texte AE/CCAP.

    Cherche les patterns courants : P = P0 × [...], indices BT/TP,
    mentions de révision/actualisation.

    Returns:
        Dict avec index_detected, formula_found, is_revisable, ou None.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Détecter si le marché est révisable
    is_revisable = any(kw in text_lower for kw in [
        "révision de prix", "prix révisable", "prix révisés",
        "formule de révision", "clause de révision",
        "actualisation", "prix actualisé",
    ])

    is_ferme = any(kw in text_lower for kw in [
        "prix ferme", "prix forfaitaire ferme",
        "non révisable", "non actualisable",
    ])

    # Détecter l'indice utilisé
    detected_indexes: list[str] = []
    for idx in PRICE_INDEXES:
        code_lower = idx.code.lower()
        if code_lower in text_lower or idx.code in text:
            detected_indexes.append(idx.code)

    # Détecter des patterns de formule
    formula_pattern = re.search(
        r"P\s*=\s*P0?\s*[×x\*]\s*\[.*?\]",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    formula_found = formula_pattern.group(0) if formula_pattern else None

    if not is_revisable and not is_ferme and not detected_indexes:
        return None

    return {
        "is_revisable": is_revisable and not is_ferme,
        "is_ferme": is_ferme,
        "detected_indexes": detected_indexes,
        "formula_found": formula_found,
        "recommendation": (
            "Marché à prix ferme — pas de révision possible."
            if is_ferme else
            f"Marché révisable — indice(s) détecté(s) : {', '.join(detected_indexes) or 'non précisé'}."
            if is_revisable else
            "Aucune clause de révision claire détectée."
        ),
    }


def get_all_price_indexes() -> list[dict[str, Any]]:
    """Retourne tous les indices de prix disponibles."""
    return [
        {
            "code": idx.code,
            "nom": idx.nom,
            "description": idx.description,
            "base_value": idx.base_value,
            "latest_value": idx.latest_value,
            "latest_date": idx.latest_date,
            "variation_pct": round((idx.latest_value / idx.base_value - 1) * 100, 1),
        }
        for idx in PRICE_INDEXES
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# COEFFICIENTS GÉOGRAPHIQUES — écart constaté vs moyenne nationale
# Source : indices régionaux FFB / INSEE BT01 (2024)
# ═══════════════════════════════════════════════════════════════════════════════

COEFFICIENTS_GEOGRAPHIQUES: dict[str, float] = {
    "ile-de-france": 1.25,      # +25% vs moyenne nationale
    "paris": 1.30,              # +30%
    "hauts-de-seine": 1.28,
    "provence-alpes-cote-d-azur": 1.10,
    "auvergne-rhone-alpes": 1.05,
    "occitanie": 1.00,
    "nouvelle-aquitaine": 0.98,
    "bretagne": 0.95,
    "normandie": 0.95,
    "pays-de-la-loire": 0.97,
    "grand-est": 0.95,
    "bourgogne-franche-comte": 0.93,
    "centre-val-de-loire": 0.95,
    "hauts-de-france": 0.95,
    "corse": 1.15,              # +15% (insularité)
    "guadeloupe": 1.35,
    "martinique": 1.35,
    "guyane": 1.40,
    "la-reunion": 1.30,
    "mayotte": 1.50,
    "france": 1.00,             # Moyenne nationale (défaut)
}


def get_geo_coefficient(region: str) -> float:
    """Retourne le coefficient géographique pour une région donnée."""
    key = _normalize(region).replace(" ", "-")
    return COEFFICIENTS_GEOGRAPHIQUES.get(key, 1.00)


# ═══════════════════════════════════════════════════════════════════════════════
# RÉFÉRENTIEL DE PRIX BTP — FRANCE MÉTROPOLITAINE 2024
# Sources : moyennes constatées marchés publics attribués, indices BT/TP
#           (INSEE), publications FFB, FNTP, Untec. Fourchettes indicatives.
# ═══════════════════════════════════════════════════════════════════════════════

_SOURCE = "Moyennes marchés publics France 2024 (ajusté 2026 +8%)"

@dataclass(frozen=True)
class PricingEntry:
    """Entrée du référentiel de prix BTP."""
    nom_fr: str
    unite: str
    prix_min_eur: float
    prix_max_eur: float
    prix_moyen_eur: float
    source: str
    categorie: str  # Gros oeuvre, Second oeuvre, VRD, Lot technique, Démolition/Désamiantage
    keywords: tuple[str, ...]  # Mots-clés pour la recherche fuzzy
    update_date: str = "2026-03"  # Date de dernière mise à jour du prix


# ── GROS OEUVRE ──────────────────────────────────────────────────────────────

GROS_OEUVRE: list[PricingEntry] = [
    PricingEntry(
        nom_fr="Terrassement en pleine masse",
        unite="m3",
        prix_min_eur=8.0,
        prix_max_eur=25.0,
        prix_moyen_eur=15.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("terrassement", "déblai", "excavation", "fouille", "pleine masse"),
    ),
    PricingEntry(
        nom_fr="Terrassement en rigole / tranchée",
        unite="m3",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("terrassement", "rigole", "tranchée", "fouille", "canalisation"),
    ),
    PricingEntry(
        nom_fr="Remblaiement compacté",
        unite="m3",
        prix_min_eur=10.0,
        prix_max_eur=30.0,
        prix_moyen_eur=18.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("remblai", "remblaiement", "compactage", "compacté"),
    ),
    PricingEntry(
        nom_fr="Fondations superficielles (semelles filantes)",
        unite="ml",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("fondation", "semelle", "filante", "superficielle"),
    ),
    PricingEntry(
        nom_fr="Fondations profondes (pieux forés)",
        unite="ml",
        prix_min_eur=150.0,
        prix_max_eur=500.0,
        prix_moyen_eur=300.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("fondation", "pieu", "foré", "profonde", "micropieu"),
    ),
    PricingEntry(
        nom_fr="Béton armé coulé en place (voiles, poteaux, poutres)",
        unite="m3",
        prix_min_eur=250.0,
        prix_max_eur=500.0,
        prix_moyen_eur=350.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("béton", "armé", "coulé", "voile", "poteau", "poutre", "coffrage"),
    ),
    PricingEntry(
        nom_fr="Béton armé pour dallage",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=90.0,
        prix_moyen_eur=60.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("béton", "dallage", "dalle", "radier", "plancher"),
    ),
    PricingEntry(
        nom_fr="Maçonnerie parpaings 20cm",
        unite="m2",
        prix_min_eur=45.0,
        prix_max_eur=85.0,
        prix_moyen_eur=62.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("maçonnerie", "parpaing", "agglo", "bloc", "béton", "mur"),
    ),
    PricingEntry(
        nom_fr="Maçonnerie briques",
        unite="m2",
        prix_min_eur=55.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("maçonnerie", "brique", "mur", "cloison"),
    ),
    PricingEntry(
        nom_fr="Charpente bois traditionnelle",
        unite="m2",
        prix_min_eur=80.0,
        prix_max_eur=180.0,
        prix_moyen_eur=120.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("charpente", "bois", "traditionnelle", "fermette", "toiture"),
    ),
    PricingEntry(
        nom_fr="Charpente métallique",
        unite="kg",
        prix_min_eur=3.5,
        prix_max_eur=8.0,
        prix_moyen_eur=5.5,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("charpente", "métallique", "acier", "structure", "portique"),
    ),
    PricingEntry(
        nom_fr="Couverture tuiles",
        unite="m2",
        prix_min_eur=50.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("couverture", "tuile", "toiture", "toit"),
    ),
    PricingEntry(
        nom_fr="Couverture bac acier",
        unite="m2",
        prix_min_eur=30.0,
        prix_max_eur=70.0,
        prix_moyen_eur=48.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("couverture", "bac", "acier", "tôle", "toiture"),
    ),
    PricingEntry(
        nom_fr="Étanchéité toiture terrasse (bicouche)",
        unite="m2",
        prix_min_eur=35.0,
        prix_max_eur=80.0,
        prix_moyen_eur=55.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("étanchéité", "toiture", "terrasse", "bicouche", "membrane"),
    ),
    PricingEntry(
        nom_fr="Isolation thermique extérieure (ITE)",
        unite="m2",
        prix_min_eur=80.0,
        prix_max_eur=180.0,
        prix_moyen_eur=130.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("isolation", "thermique", "extérieure", "ite", "polystyrène", "laine"),
    ),
    PricingEntry(
        nom_fr="Isolation thermique intérieure",
        unite="m2",
        prix_min_eur=25.0,
        prix_max_eur=65.0,
        prix_moyen_eur=40.0,
        source=_SOURCE,
        categorie="Gros oeuvre",
        keywords=("isolation", "thermique", "intérieure", "doublage", "placo"),
    ),
]

# ── SECOND OEUVRE ────────────────────────────────────────────────────────────

SECOND_OEUVRE: list[PricingEntry] = [
    PricingEntry(
        nom_fr="Plomberie sanitaire — point d'eau complet",
        unite="U",
        prix_min_eur=800.0,
        prix_max_eur=2000.0,
        prix_moyen_eur=1200.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("plomberie", "sanitaire", "point d'eau", "lavabo", "évier"),
    ),
    PricingEntry(
        nom_fr="Plomberie — alimentation eau (cuivre)",
        unite="ml",
        prix_min_eur=25.0,
        prix_max_eur=60.0,
        prix_moyen_eur=40.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("plomberie", "alimentation", "eau", "cuivre", "tuyau", "canalisation"),
    ),
    PricingEntry(
        nom_fr="Plomberie — évacuation PVC",
        unite="ml",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("plomberie", "évacuation", "pvc", "eaux usées", "eaux vannes"),
    ),
    PricingEntry(
        nom_fr="Électricité — point lumineux",
        unite="U",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("électricité", "point", "lumineux", "éclairage", "lumière"),
    ),
    PricingEntry(
        nom_fr="Électricité — prise de courant",
        unite="U",
        prix_min_eur=50.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("électricité", "prise", "courant", "2p+t"),
    ),
    PricingEntry(
        nom_fr="Électricité — tableau électrique (TGBT)",
        unite="U",
        prix_min_eur=1500.0,
        prix_max_eur=8000.0,
        prix_moyen_eur=3500.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("électricité", "tableau", "tgbt", "armoire", "disjoncteur"),
    ),
    PricingEntry(
        nom_fr="Menuiseries extérieures PVC (fenêtre standard)",
        unite="U",
        prix_min_eur=250.0,
        prix_max_eur=700.0,
        prix_moyen_eur=450.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("menuiserie", "fenêtre", "pvc", "extérieure", "châssis"),
    ),
    PricingEntry(
        nom_fr="Menuiseries extérieures aluminium (fenêtre)",
        unite="U",
        prix_min_eur=400.0,
        prix_max_eur=1200.0,
        prix_moyen_eur=700.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("menuiserie", "fenêtre", "aluminium", "alu", "extérieure"),
    ),
    PricingEntry(
        nom_fr="Menuiseries intérieures — porte standard",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=600.0,
        prix_moyen_eur=350.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("menuiserie", "porte", "intérieure", "bloc-porte", "standard"),
    ),
    PricingEntry(
        nom_fr="Menuiseries intérieures — porte coupe-feu",
        unite="U",
        prix_min_eur=500.0,
        prix_max_eur=1500.0,
        prix_moyen_eur=900.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("menuiserie", "porte", "coupe-feu", "cf", "ei30", "ei60", "ei120"),
    ),
    PricingEntry(
        nom_fr="Peinture intérieure (2 couches)",
        unite="m2",
        prix_min_eur=12.0,
        prix_max_eur=30.0,
        prix_moyen_eur=18.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("peinture", "intérieure", "mur", "plafond", "ravalement"),
    ),
    PricingEntry(
        nom_fr="Peinture extérieure / ravalement",
        unite="m2",
        prix_min_eur=20.0,
        prix_max_eur=55.0,
        prix_moyen_eur=35.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("peinture", "extérieure", "ravalement", "façade", "enduit"),
    ),
    PricingEntry(
        nom_fr="Carrelage sol (pose comprise)",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("carrelage", "sol", "grès", "cérame", "faïence", "dallage"),
    ),
    PricingEntry(
        nom_fr="Carrelage mural (pose comprise)",
        unite="m2",
        prix_min_eur=45.0,
        prix_max_eur=110.0,
        prix_moyen_eur=70.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("carrelage", "mural", "faïence", "mur", "salle de bain"),
    ),
    PricingEntry(
        nom_fr="Revêtement de sol souple (PVC / lino)",
        unite="m2",
        prix_min_eur=20.0,
        prix_max_eur=55.0,
        prix_moyen_eur=35.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("revêtement", "sol", "pvc", "lino", "souple", "vinyle"),
    ),
    PricingEntry(
        nom_fr="Parquet stratifié (pose comprise)",
        unite="m2",
        prix_min_eur=25.0,
        prix_max_eur=70.0,
        prix_moyen_eur=45.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("parquet", "stratifié", "flottant", "bois"),
    ),
    PricingEntry(
        nom_fr="Cloison sèche placo BA13 (double parement)",
        unite="m2",
        prix_min_eur=35.0,
        prix_max_eur=70.0,
        prix_moyen_eur=50.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("cloison", "placo", "plâtre", "ba13", "sèche", "doublage"),
    ),
    PricingEntry(
        nom_fr="Faux plafond suspendu (dalles 60x60)",
        unite="m2",
        prix_min_eur=30.0,
        prix_max_eur=70.0,
        prix_moyen_eur=48.0,
        source=_SOURCE,
        categorie="Second oeuvre",
        keywords=("faux plafond", "suspendu", "dalle", "plafond", "acoustique"),
    ),
]

# ── VRD (Voirie et Réseaux Divers) ──────────────────────────────────────────

VRD: list[PricingEntry] = [
    PricingEntry(
        nom_fr="Voirie — enrobé bitumineux (couche de roulement)",
        unite="m2",
        prix_min_eur=15.0,
        prix_max_eur=40.0,
        prix_moyen_eur=25.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("voirie", "enrobé", "bitume", "bitumineux", "chaussée", "roulement"),
    ),
    PricingEntry(
        nom_fr="Voirie — couche de base grave ciment",
        unite="m2",
        prix_min_eur=12.0,
        prix_max_eur=30.0,
        prix_moyen_eur=20.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("voirie", "grave", "ciment", "base", "fondation", "gnta"),
    ),
    PricingEntry(
        nom_fr="Bordures béton T2",
        unite="ml",
        prix_min_eur=18.0,
        prix_max_eur=40.0,
        prix_moyen_eur=28.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("bordure", "béton", "t2", "caniveau", "trottoir"),
    ),
    PricingEntry(
        nom_fr="Trottoir dallé / pavé",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("trottoir", "dalle", "pavé", "piéton", "cheminement"),
    ),
    PricingEntry(
        nom_fr="Réseau assainissement — canalisation PVC DN200",
        unite="ml",
        prix_min_eur=45.0,
        prix_max_eur=120.0,
        prix_moyen_eur=75.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("assainissement", "canalisation", "pvc", "réseau", "eaux usées", "eaux pluviales"),
    ),
    PricingEntry(
        nom_fr="Réseau assainissement — regard béton",
        unite="U",
        prix_min_eur=400.0,
        prix_max_eur=1200.0,
        prix_moyen_eur=700.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("assainissement", "regard", "béton", "boîte", "branchement"),
    ),
    PricingEntry(
        nom_fr="Réseau eau potable (PE/PEHD DN63)",
        unite="ml",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("eau potable", "aep", "pehd", "réseau", "adduction"),
    ),
    PricingEntry(
        nom_fr="Éclairage public — mât + luminaire LED",
        unite="U",
        prix_min_eur=2000.0,
        prix_max_eur=5000.0,
        prix_moyen_eur=3200.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("éclairage", "public", "mât", "candélabre", "luminaire", "led"),
    ),
    PricingEntry(
        nom_fr="Tranchée pour réseaux secs / humides",
        unite="ml",
        prix_min_eur=20.0,
        prix_max_eur=60.0,
        prix_moyen_eur=38.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("tranchée", "réseau", "sec", "humide", "gaine", "fourreau"),
    ),
    PricingEntry(
        nom_fr="Espace vert — engazonnement",
        unite="m2",
        prix_min_eur=5.0,
        prix_max_eur=15.0,
        prix_moyen_eur=9.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("espace vert", "gazon", "engazonnement", "pelouse", "semis"),
    ),
    PricingEntry(
        nom_fr="Espace vert — plantation arbre tige",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=800.0,
        prix_moyen_eur=450.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("espace vert", "arbre", "plantation", "tige", "végétal"),
    ),
    PricingEntry(
        nom_fr="Clôture grillagée (hauteur 2m)",
        unite="ml",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source=_SOURCE,
        categorie="VRD",
        keywords=("clôture", "grillage", "grillagée", "panneau", "soudé"),
    ),
]

# ── LOT TECHNIQUE (CVC, Plomberie sanitaire, Courants forts/faibles) ────────

LOT_TECHNIQUE: list[PricingEntry] = [
    PricingEntry(
        nom_fr="CVC — chaudière gaz condensation",
        unite="U",
        prix_min_eur=4000.0,
        prix_max_eur=12000.0,
        prix_moyen_eur=7500.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "chaudière", "gaz", "condensation", "chauffage"),
    ),
    PricingEntry(
        nom_fr="CVC — pompe à chaleur air/eau",
        unite="U",
        prix_min_eur=8000.0,
        prix_max_eur=25000.0,
        prix_moyen_eur=15000.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "pac", "pompe", "chaleur", "air", "eau", "thermodynamique"),
    ),
    PricingEntry(
        nom_fr="CVC — radiateur acier (type 22, 1000mm)",
        unite="U",
        prix_min_eur=150.0,
        prix_max_eur=400.0,
        prix_moyen_eur=250.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "radiateur", "acier", "chauffage", "émetteur"),
    ),
    PricingEntry(
        nom_fr="CVC — plancher chauffant hydraulique",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=90.0,
        prix_moyen_eur=60.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "plancher", "chauffant", "hydraulique", "sol"),
    ),
    PricingEntry(
        nom_fr="CVC — gaine de ventilation tôle galvanisée",
        unite="ml",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "ventilation", "gaine", "vmc", "tôle", "galvanisée"),
    ),
    PricingEntry(
        nom_fr="CVC — CTA (Centrale de Traitement d'Air)",
        unite="U",
        prix_min_eur=5000.0,
        prix_max_eur=30000.0,
        prix_moyen_eur=15000.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "cta", "centrale", "traitement", "air", "climatisation"),
    ),
    PricingEntry(
        nom_fr="CVC — split / climatiseur mono-split",
        unite="U",
        prix_min_eur=1200.0,
        prix_max_eur=3500.0,
        prix_moyen_eur=2200.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("cvc", "split", "climatiseur", "clim", "froid"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — WC complet (pose)",
        unite="U",
        prix_min_eur=350.0,
        prix_max_eur=900.0,
        prix_moyen_eur=550.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("plomberie", "wc", "toilette", "sanitaire", "cuvette"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — douche complète (receveur + robinetterie + paroi)",
        unite="U",
        prix_min_eur=800.0,
        prix_max_eur=2500.0,
        prix_moyen_eur=1400.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("plomberie", "douche", "receveur", "bac", "robinetterie"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — chauffe-eau thermodynamique",
        unite="U",
        prix_min_eur=2000.0,
        prix_max_eur=5000.0,
        prix_moyen_eur=3200.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("plomberie", "chauffe-eau", "ballon", "ecs", "thermodynamique"),
    ),
    PricingEntry(
        nom_fr="Courants forts — câblage VDI (prise RJ45)",
        unite="U",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("courant", "faible", "vdi", "rj45", "réseau", "informatique"),
    ),
    PricingEntry(
        nom_fr="Courants forts — chemin de câbles",
        unite="ml",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("courant", "chemin", "câble", "goulotte", "électrique"),
    ),
    PricingEntry(
        nom_fr="Sécurité incendie — détecteur (DAI)",
        unite="U",
        prix_min_eur=60.0,
        prix_max_eur=200.0,
        prix_moyen_eur=120.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("incendie", "détecteur", "dai", "ssi", "alarme", "sécurité"),
    ),
    PricingEntry(
        nom_fr="Sécurité incendie — extincteur ABC",
        unite="U",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("incendie", "extincteur", "abc", "sécurité"),
    ),
    PricingEntry(
        nom_fr="Ascenseur (cabine standard, 8 personnes, 5 niveaux)",
        unite="U",
        prix_min_eur=35000.0,
        prix_max_eur=80000.0,
        prix_moyen_eur=55000.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("ascenseur", "élévateur", "monte-charge", "cabine"),
    ),
    PricingEntry(
        nom_fr="Photovoltaïque — panneau solaire (pose sur toiture)",
        unite="Wc",
        prix_min_eur=1.5,
        prix_max_eur=3.0,
        prix_moyen_eur=2.2,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("photovoltaïque", "solaire", "panneau", "pv", "wc"),
    ),
    PricingEntry(
        nom_fr="GTB / GTC — point de comptage / mesure",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=600.0,
        prix_moyen_eur=380.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("gtb", "gtc", "gestion", "technique", "bâtiment", "automate"),
    ),
    PricingEntry(
        nom_fr="Borne de recharge véhicule électrique (IRVE 7-22 kW)",
        unite="U",
        prix_min_eur=2500.0,
        prix_max_eur=8000.0,
        prix_moyen_eur=4500.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("borne", "recharge", "irve", "véhicule", "électrique", "ev", "wallbox"),
    ),
    PricingEntry(
        nom_fr="Géothermie — sonde verticale (forage + sonde)",
        unite="ml",
        prix_min_eur=50.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("géothermie", "sonde", "forage", "vertical", "pac", "sol"),
    ),
    PricingEntry(
        nom_fr="Domotique / Smart Building — point de commande KNX",
        unite="U",
        prix_min_eur=300.0,
        prix_max_eur=800.0,
        prix_moyen_eur=500.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("domotique", "smart", "knx", "commande", "automatisation", "bâtiment"),
    ),
    PricingEntry(
        nom_fr="Vidéosurveillance — caméra IP + installation",
        unite="U",
        prix_min_eur=500.0,
        prix_max_eur=2000.0,
        prix_moyen_eur=1100.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("vidéosurveillance", "caméra", "ip", "sécurité", "cctv", "surveillance"),
    ),
    PricingEntry(
        nom_fr="Contrôle d'accès — lecteur badge + gâche",
        unite="U",
        prix_min_eur=400.0,
        prix_max_eur=1500.0,
        prix_moyen_eur=800.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("contrôle", "accès", "badge", "gâche", "lecteur", "sûreté"),
    ),
    PricingEntry(
        nom_fr="Désenfumage mécanique — extracteur + gaine",
        unite="U",
        prix_min_eur=3000.0,
        prix_max_eur=12000.0,
        prix_moyen_eur=6500.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("désenfumage", "extracteur", "ventilateur", "incendie", "fumée"),
    ),
    PricingEntry(
        nom_fr="Sprinkler — réseau sprinklage (installation)",
        unite="m2",
        prix_min_eur=25.0,
        prix_max_eur=70.0,
        prix_moyen_eur=45.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("sprinkler", "sprinklage", "extinction", "automatique", "incendie"),
    ),
    PricingEntry(
        nom_fr="Panneau solaire thermique (ECS)",
        unite="m2",
        prix_min_eur=500.0,
        prix_max_eur=1200.0,
        prix_moyen_eur=800.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("solaire", "thermique", "ecs", "panneau", "capteur", "eau", "chaude"),
    ),
    PricingEntry(
        nom_fr="Groupe électrogène (secours, 100 kVA)",
        unite="U",
        prix_min_eur=15000.0,
        prix_max_eur=45000.0,
        prix_moyen_eur=28000.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("groupe", "électrogène", "secours", "onduleur", "kva", "alimentation"),
    ),
    PricingEntry(
        nom_fr="Onduleur / ASI (alimentation sans interruption, 10 kVA)",
        unite="U",
        prix_min_eur=5000.0,
        prix_max_eur=18000.0,
        prix_moyen_eur=10000.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("onduleur", "asi", "ups", "secours", "informatique"),
    ),
    PricingEntry(
        nom_fr="Toiture végétalisée extensive",
        unite="m2",
        prix_min_eur=50.0,
        prix_max_eur=130.0,
        prix_moyen_eur=85.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("toiture", "végétalisée", "extensive", "sedum", "verte"),
    ),
    PricingEntry(
        nom_fr="Réseau gaz (canalisation PE, branchement)",
        unite="ml",
        prix_min_eur=35.0,
        prix_max_eur=100.0,
        prix_moyen_eur=60.0,
        source=_SOURCE,
        categorie="Lot technique",
        keywords=("gaz", "canalisation", "pe", "réseau", "branchement"),
    ),
]

# ── DÉMOLITION / DÉSAMIANTAGE / RÉNOVATION ─────────────────────────────────

DEMO_RENOVATION: list[PricingEntry] = [
    PricingEntry(
        nom_fr="Démolition bâtiment (structure béton, hors désamiantage)",
        unite="m3",
        prix_min_eur=25.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("démolition", "déconstruction", "béton", "bâtiment", "curage"),
    ),
    PricingEntry(
        nom_fr="Curage intérieur complet",
        unite="m2",
        prix_min_eur=15.0,
        prix_max_eur=50.0,
        prix_moyen_eur=30.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("curage", "intérieur", "démolition", "dépollution", "strip-out"),
    ),
    PricingEntry(
        nom_fr="Désamiantage — retrait amiante friable (confinement)",
        unite="m2",
        prix_min_eur=150.0,
        prix_max_eur=500.0,
        prix_moyen_eur=300.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("désamiantage", "amiante", "friable", "confinement", "retrait", "ss3"),
    ),
    PricingEntry(
        nom_fr="Désamiantage — retrait amiante non-friable (dalles, toiture)",
        unite="m2",
        prix_min_eur=30.0,
        prix_max_eur=120.0,
        prix_moyen_eur=65.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("désamiantage", "amiante", "non-friable", "dalles", "fibrociment", "ss4"),
    ),
    PricingEntry(
        nom_fr="Déplombage / décontamination plomb",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=150.0,
        prix_moyen_eur=85.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("plomb", "déplombage", "décontamination", "saturnisme", "peinture"),
    ),
    PricingEntry(
        nom_fr="Ravalement de façade (enduit + peinture)",
        unite="m2",
        prix_min_eur=50.0,
        prix_max_eur=130.0,
        prix_moyen_eur=85.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("ravalement", "façade", "enduit", "peinture", "extérieur", "rénovation"),
    ),
    PricingEntry(
        nom_fr="Mise en accessibilité PMR (rampe + bande podotactile)",
        unite="U",
        prix_min_eur=2000.0,
        prix_max_eur=8000.0,
        prix_moyen_eur=4500.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("accessibilité", "pmr", "rampe", "handicapé", "bande", "podotactile", "erp"),
    ),
    PricingEntry(
        nom_fr="Diagnostic amiante avant travaux (DAT)",
        unite="U",
        prix_min_eur=800.0,
        prix_max_eur=3000.0,
        prix_moyen_eur=1600.0,
        source=_SOURCE,
        categorie="Démolition / Rénovation",
        keywords=("diagnostic", "amiante", "dat", "repérage", "avant", "travaux"),
    ),
]

# ── Référentiel consolidé ───────────────────────────────────────────────────

PRICING_REFERENCE: list[PricingEntry] = GROS_OEUVRE + SECOND_OEUVRE + VRD + LOT_TECHNIQUE + DEMO_RENOVATION

# Index par catégorie pour accès rapide
_REFERENCE_BY_CATEGORY: dict[str, list[PricingEntry]] = {}
for _entry in PRICING_REFERENCE:
    _REFERENCE_BY_CATEGORY.setdefault(_entry.categorie, []).append(_entry)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PUBLIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Normalise un texte pour la recherche (minuscules, sans accents simplifiés, sans ponctuation)."""
    text = text.lower().strip()
    # Remplacements d'accents courants
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "ù": "u", "û": "u", "ü": "u",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ç": "c",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Supprimer la ponctuation sauf les espaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _match_score(query_words: list[str], entry: PricingEntry) -> float:
    """Calcule un score de correspondance (0.0 - 1.0) entre une requête et une entrée."""
    if not query_words:
        return 0.0

    # Construire le texte de recherche de l'entrée
    entry_text = _normalize(
        entry.nom_fr + " " + " ".join(entry.keywords) + " " + entry.categorie
    )
    entry_words = set(entry_text.split())

    matched = 0
    for qw in query_words:
        # Match exact
        if qw in entry_words:
            matched += 1.0
        # Match partiel (le mot-clé est contenu dans un mot de l'entrée)
        elif any(qw in ew for ew in entry_words):
            matched += 0.6
        # Match inverse (un mot de l'entrée est contenu dans le mot-clé)
        elif any(ew in qw for ew in entry_words if len(ew) > 3):
            matched += 0.4

    return matched / len(query_words)


def get_pricing_reference(keyword: str) -> list[dict[str, Any]]:
    """Recherche dans le référentiel de prix BTP par mot-clé.

    Args:
        keyword: Mot-clé ou description du poste recherché
            (ex: "béton armé", "plomberie", "enrobé").

    Returns:
        Liste de dictionnaires triés par pertinence décroissante, chaque dict avec :
        - nom_fr, unite, prix_min_eur, prix_max_eur, prix_moyen_eur, source, categorie
    """
    query_words = _normalize(keyword).split()
    if not query_words:
        return []

    scored: list[tuple[float, PricingEntry]] = []
    for entry in PRICING_REFERENCE:
        score = _match_score(query_words, entry)
        if score >= 0.3:  # Seuil minimum de pertinence
            scored.append((score, entry))

    # Tri par score décroissant
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[dict[str, Any]] = []
    adj = PRICE_ADJUSTMENT_2026
    for score, entry in scored[:10]:  # Max 10 résultats
        results.append({
            "nom_fr": entry.nom_fr,
            "unite": entry.unite,
            "prix_min_eur": round(entry.prix_min_eur * adj, 2),
            "prix_max_eur": round(entry.prix_max_eur * adj, 2),
            "prix_moyen_eur": round(entry.prix_moyen_eur * adj, 2),
            "source": entry.source,
            "categorie": entry.categorie,
            "relevance_score": round(score, 2),
            "update_date": entry.update_date,
            "adjustment_2026": adj,
        })

    return results


def _find_best_match(designation: str) -> PricingEntry | None:
    """Trouve l'entrée du référentiel la plus proche d'une désignation DPGF."""
    query_words = _normalize(designation).split()
    if not query_words:
        return None

    best_score = 0.0
    best_entry: PricingEntry | None = None

    for entry in PRICING_REFERENCE:
        score = _match_score(query_words, entry)
        if score > best_score:
            best_score = score
            best_entry = entry

    # Seuil minimum pour éviter les faux positifs
    if best_score < 0.3:
        return None

    return best_entry


def _parse_price(value: Any) -> float | None:
    """Convertit une valeur de prix (str, int, float) en float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        cleaned = re.sub(r"[€$\s\xa0]", "", cleaned)
        cleaned = cleaned.replace(",", ".")
        # Format 1.234.567,89
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def check_dpgf_pricing(rows: list[dict], region: str = "france") -> list[dict[str, Any]]:
    """Compare chaque ligne DPGF au référentiel et signale les anomalies.

    Args:
        rows: Liste de dictionnaires représentant les lignes DPGF. Chaque dict
            doit contenir au minimum :
            - designation (str) : description du poste
            - prix_unitaire (str|float) : prix unitaire HT
            Optionnels : unite (str), quantite (str|float), montant_ht (str|float)
        region: Région géographique pour ajuster les prix (défaut: "france").
            Exemple: "ile-de-france", "provence-alpes-cote-d-azur", "bretagne".

    Returns:
        Liste de dictionnaires, un par ligne, avec :
        - designation : str -- désignation originale
        - prix_unitaire : float|None -- prix unitaire de la ligne DPGF
        - reference_match : str|None -- nom du poste de référence le plus proche
        - reference_unite : str|None -- unité de référence
        - reference_prix_min : float|None -- prix min référentiel (ajusté région)
        - reference_prix_max : float|None -- prix max référentiel (ajusté région)
        - reference_prix_moyen : float|None -- prix moyen référentiel (ajusté région)
        - status : str -- "SOUS_EVALUE" | "NORMAL" | "SUR_EVALUE" | "INCONNU"
        - ratio_vs_moyen : float|None -- ratio prix DPGF / prix moyen référentiel
        - alerte : str -- message d'alerte lisible (vide si NORMAL ou INCONNU)
        - categorie : str|None -- catégorie BTP du poste de référence
        - geo_coefficient : float -- coefficient géographique appliqué
    """
    geo_coeff = get_geo_coefficient(region)
    results: list[dict[str, Any]] = []

    for row in rows:
        designation = str(row.get("designation", "") or "").strip()
        prix_unitaire = _parse_price(row.get("prix_unitaire"))

        # Chercher le meilleur match dans le référentiel
        match = _find_best_match(designation)

        if match is None or prix_unitaire is None:
            results.append({
                "designation": designation,
                "prix_unitaire": prix_unitaire,
                "reference_match": None,
                "reference_unite": None,
                "reference_prix_min": None,
                "reference_prix_max": None,
                "reference_prix_moyen": None,
                "status": "INCONNU",
                "ratio_vs_moyen": None,
                "alerte": "",
                "categorie": None,
                "geo_coefficient": geo_coeff,
            })
            continue

        # Appliquer coefficient géographique + ajustement 2026
        total_adj = geo_coeff * PRICE_ADJUSTMENT_2026
        adj_min = round(match.prix_min_eur * total_adj, 2)
        adj_max = round(match.prix_max_eur * total_adj, 2)
        adj_moyen = round(match.prix_moyen_eur * total_adj, 2)

        # Calculer le ratio vs prix moyen ajusté
        ratio = round(prix_unitaire / adj_moyen, 2) if adj_moyen > 0 else None

        # Déterminer le statut avec prix ajustés
        if prix_unitaire < adj_min:
            status = "SOUS_EVALUE"
            ecart_pct = round((1 - prix_unitaire / adj_min) * 100)
            alerte = (
                f"Prix unitaire ({prix_unitaire:.2f} EUR/{match.unite}) inférieur "
                f"au minimum référentiel ajusté ({adj_min:.2f} EUR/{match.unite}). "
                f"Écart : -{ecart_pct}% sous le plancher."
            )
        elif prix_unitaire > adj_max:
            status = "SUR_EVALUE"
            ecart_pct = round((prix_unitaire / adj_max - 1) * 100)
            alerte = (
                f"Prix unitaire ({prix_unitaire:.2f} EUR/{match.unite}) supérieur "
                f"au maximum référentiel ajusté ({adj_max:.2f} EUR/{match.unite}). "
                f"Écart : +{ecart_pct}% au-dessus du plafond."
            )
        else:
            status = "NORMAL"
            alerte = ""

        results.append({
            "designation": designation,
            "prix_unitaire": prix_unitaire,
            "reference_match": match.nom_fr,
            "reference_unite": match.unite,
            "reference_prix_min": adj_min,
            "reference_prix_max": adj_max,
            "reference_prix_moyen": adj_moyen,
            "status": status,
            "ratio_vs_moyen": ratio,
            "alerte": alerte,
            "categorie": match.categorie,
            "geo_coefficient": geo_coeff,
        })

    # Log un résumé
    total = len(results)
    sous_eval = sum(1 for r in results if r["status"] == "SOUS_EVALUE")
    sur_eval = sum(1 for r in results if r["status"] == "SUR_EVALUE")
    normaux = sum(1 for r in results if r["status"] == "NORMAL")
    inconnus = sum(1 for r in results if r["status"] == "INCONNU")

    logger.info(
        f"Analyse DPGF pricing — {total} postes : "
        f"{normaux} normaux, {sous_eval} sous-évalués, "
        f"{sur_eval} surévalués, {inconnus} inconnus"
    )

    return results


def get_pricing_summary() -> dict[str, Any]:
    """Retourne un résumé du référentiel de prix pour affichage.

    Returns:
        Dictionnaire avec :
        - total_entries: int -- nombre total d'entrées
        - categories: dict[str, int] -- nombre d'entrées par catégorie
        - source: str -- source des données
        - year: int -- année de référence
    """
    categories: dict[str, int] = {}
    for entry in PRICING_REFERENCE:
        categories[entry.categorie] = categories.get(entry.categorie, 0) + 1

    return {
        "total_entries": len(PRICING_REFERENCE),
        "categories": categories,
        "source": "Moyennes marchés publics France 2024 (ajusté 2026 +8%, indicatif ±30%)",
        "year": 2024,
        "adjustment_year": 2026,
        "adjustment_coefficient": PRICE_ADJUSTMENT_2026,
        "price_indexes": [idx.code for idx in PRICE_INDEXES],
    }
