"""Référentiel de prix BTP + analyse des postes DPGF.

Module statique de référence prix (aucun appel LLM). Contient un dictionnaire
de 50+ types de postes BTP courants avec fourchettes de prix indicatifs
2024 France métropolitaine, sources Batiprix / indices BTP publics.

Fonctions principales :
- check_dpgf_pricing() : compare les lignes DPGF au référentiel et signale
  les postes sous-évalués, surévalués ou normaux.
- get_pricing_reference() : recherche dans le référentiel par mot-clé.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# RÉFÉRENTIEL DE PRIX BTP — FRANCE MÉTROPOLITAINE 2024
# Sources indicatives : Batiprix, indices BTP publics, moyennes constatées
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PricingEntry:
    """Entrée du référentiel de prix BTP."""
    nom_fr: str
    unite: str
    prix_min_eur: float
    prix_max_eur: float
    prix_moyen_eur: float
    source: str
    categorie: str  # Gros oeuvre, Second oeuvre, VRD, Lot technique
    keywords: tuple[str, ...]  # Mots-clés pour la recherche fuzzy


# ── GROS OEUVRE ──────────────────────────────────────────────────────────────

GROS_OEUVRE: list[PricingEntry] = [
    PricingEntry(
        nom_fr="Terrassement en pleine masse",
        unite="m3",
        prix_min_eur=8.0,
        prix_max_eur=25.0,
        prix_moyen_eur=15.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("terrassement", "déblai", "excavation", "fouille", "pleine masse"),
    ),
    PricingEntry(
        nom_fr="Terrassement en rigole / tranchée",
        unite="m3",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("terrassement", "rigole", "tranchée", "fouille", "canalisation"),
    ),
    PricingEntry(
        nom_fr="Remblaiement compacté",
        unite="m3",
        prix_min_eur=10.0,
        prix_max_eur=30.0,
        prix_moyen_eur=18.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("remblai", "remblaiement", "compactage", "compacté"),
    ),
    PricingEntry(
        nom_fr="Fondations superficielles (semelles filantes)",
        unite="ml",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("fondation", "semelle", "filante", "superficielle"),
    ),
    PricingEntry(
        nom_fr="Fondations profondes (pieux forés)",
        unite="ml",
        prix_min_eur=150.0,
        prix_max_eur=500.0,
        prix_moyen_eur=300.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("fondation", "pieu", "foré", "profonde", "micropieu"),
    ),
    PricingEntry(
        nom_fr="Béton armé coulé en place (voiles, poteaux, poutres)",
        unite="m3",
        prix_min_eur=250.0,
        prix_max_eur=500.0,
        prix_moyen_eur=350.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("béton", "armé", "coulé", "voile", "poteau", "poutre", "coffrage"),
    ),
    PricingEntry(
        nom_fr="Béton armé pour dallage",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=90.0,
        prix_moyen_eur=60.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("béton", "dallage", "dalle", "radier", "plancher"),
    ),
    PricingEntry(
        nom_fr="Maçonnerie parpaings 20cm",
        unite="m2",
        prix_min_eur=45.0,
        prix_max_eur=85.0,
        prix_moyen_eur=62.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("maçonnerie", "parpaing", "agglo", "bloc", "béton", "mur"),
    ),
    PricingEntry(
        nom_fr="Maçonnerie briques",
        unite="m2",
        prix_min_eur=55.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("maçonnerie", "brique", "mur", "cloison"),
    ),
    PricingEntry(
        nom_fr="Charpente bois traditionnelle",
        unite="m2",
        prix_min_eur=80.0,
        prix_max_eur=180.0,
        prix_moyen_eur=120.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("charpente", "bois", "traditionnelle", "fermette", "toiture"),
    ),
    PricingEntry(
        nom_fr="Charpente métallique",
        unite="kg",
        prix_min_eur=3.5,
        prix_max_eur=8.0,
        prix_moyen_eur=5.5,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("charpente", "métallique", "acier", "structure", "portique"),
    ),
    PricingEntry(
        nom_fr="Couverture tuiles",
        unite="m2",
        prix_min_eur=50.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("couverture", "tuile", "toiture", "toit"),
    ),
    PricingEntry(
        nom_fr="Couverture bac acier",
        unite="m2",
        prix_min_eur=30.0,
        prix_max_eur=70.0,
        prix_moyen_eur=48.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("couverture", "bac", "acier", "tôle", "toiture"),
    ),
    PricingEntry(
        nom_fr="Étanchéité toiture terrasse (bicouche)",
        unite="m2",
        prix_min_eur=35.0,
        prix_max_eur=80.0,
        prix_moyen_eur=55.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("étanchéité", "toiture", "terrasse", "bicouche", "membrane"),
    ),
    PricingEntry(
        nom_fr="Isolation thermique extérieure (ITE)",
        unite="m2",
        prix_min_eur=80.0,
        prix_max_eur=180.0,
        prix_moyen_eur=130.0,
        source="Batiprix 2024",
        categorie="Gros oeuvre",
        keywords=("isolation", "thermique", "extérieure", "ite", "polystyrène", "laine"),
    ),
    PricingEntry(
        nom_fr="Isolation thermique intérieure",
        unite="m2",
        prix_min_eur=25.0,
        prix_max_eur=65.0,
        prix_moyen_eur=40.0,
        source="Batiprix 2024",
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
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("plomberie", "sanitaire", "point d'eau", "lavabo", "évier"),
    ),
    PricingEntry(
        nom_fr="Plomberie — alimentation eau (cuivre)",
        unite="ml",
        prix_min_eur=25.0,
        prix_max_eur=60.0,
        prix_moyen_eur=40.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("plomberie", "alimentation", "eau", "cuivre", "tuyau", "canalisation"),
    ),
    PricingEntry(
        nom_fr="Plomberie — évacuation PVC",
        unite="ml",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("plomberie", "évacuation", "pvc", "eaux usées", "eaux vannes"),
    ),
    PricingEntry(
        nom_fr="Électricité — point lumineux",
        unite="U",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("électricité", "point", "lumineux", "éclairage", "lumière"),
    ),
    PricingEntry(
        nom_fr="Électricité — prise de courant",
        unite="U",
        prix_min_eur=50.0,
        prix_max_eur=120.0,
        prix_moyen_eur=80.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("électricité", "prise", "courant", "2p+t"),
    ),
    PricingEntry(
        nom_fr="Électricité — tableau électrique (TGBT)",
        unite="U",
        prix_min_eur=1500.0,
        prix_max_eur=8000.0,
        prix_moyen_eur=3500.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("électricité", "tableau", "tgbt", "armoire", "disjoncteur"),
    ),
    PricingEntry(
        nom_fr="Menuiseries extérieures PVC (fenêtre standard)",
        unite="U",
        prix_min_eur=250.0,
        prix_max_eur=700.0,
        prix_moyen_eur=450.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("menuiserie", "fenêtre", "pvc", "extérieure", "châssis"),
    ),
    PricingEntry(
        nom_fr="Menuiseries extérieures aluminium (fenêtre)",
        unite="U",
        prix_min_eur=400.0,
        prix_max_eur=1200.0,
        prix_moyen_eur=700.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("menuiserie", "fenêtre", "aluminium", "alu", "extérieure"),
    ),
    PricingEntry(
        nom_fr="Menuiseries intérieures — porte standard",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=600.0,
        prix_moyen_eur=350.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("menuiserie", "porte", "intérieure", "bloc-porte", "standard"),
    ),
    PricingEntry(
        nom_fr="Menuiseries intérieures — porte coupe-feu",
        unite="U",
        prix_min_eur=500.0,
        prix_max_eur=1500.0,
        prix_moyen_eur=900.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("menuiserie", "porte", "coupe-feu", "cf", "ei30", "ei60", "ei120"),
    ),
    PricingEntry(
        nom_fr="Peinture intérieure (2 couches)",
        unite="m2",
        prix_min_eur=12.0,
        prix_max_eur=30.0,
        prix_moyen_eur=18.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("peinture", "intérieure", "mur", "plafond", "ravalement"),
    ),
    PricingEntry(
        nom_fr="Peinture extérieure / ravalement",
        unite="m2",
        prix_min_eur=20.0,
        prix_max_eur=55.0,
        prix_moyen_eur=35.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("peinture", "extérieure", "ravalement", "façade", "enduit"),
    ),
    PricingEntry(
        nom_fr="Carrelage sol (pose comprise)",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("carrelage", "sol", "grès", "cérame", "faïence", "dallage"),
    ),
    PricingEntry(
        nom_fr="Carrelage mural (pose comprise)",
        unite="m2",
        prix_min_eur=45.0,
        prix_max_eur=110.0,
        prix_moyen_eur=70.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("carrelage", "mural", "faïence", "mur", "salle de bain"),
    ),
    PricingEntry(
        nom_fr="Revêtement de sol souple (PVC / lino)",
        unite="m2",
        prix_min_eur=20.0,
        prix_max_eur=55.0,
        prix_moyen_eur=35.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("revêtement", "sol", "pvc", "lino", "souple", "vinyle"),
    ),
    PricingEntry(
        nom_fr="Parquet stratifié (pose comprise)",
        unite="m2",
        prix_min_eur=25.0,
        prix_max_eur=70.0,
        prix_moyen_eur=45.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("parquet", "stratifié", "flottant", "bois"),
    ),
    PricingEntry(
        nom_fr="Cloison sèche placo BA13 (double parement)",
        unite="m2",
        prix_min_eur=35.0,
        prix_max_eur=70.0,
        prix_moyen_eur=50.0,
        source="Batiprix 2024",
        categorie="Second oeuvre",
        keywords=("cloison", "placo", "plâtre", "ba13", "sèche", "doublage"),
    ),
    PricingEntry(
        nom_fr="Faux plafond suspendu (dalles 60x60)",
        unite="m2",
        prix_min_eur=30.0,
        prix_max_eur=70.0,
        prix_moyen_eur=48.0,
        source="Batiprix 2024",
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
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("voirie", "enrobé", "bitume", "bitumineux", "chaussée", "roulement"),
    ),
    PricingEntry(
        nom_fr="Voirie — couche de base grave ciment",
        unite="m2",
        prix_min_eur=12.0,
        prix_max_eur=30.0,
        prix_moyen_eur=20.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("voirie", "grave", "ciment", "base", "fondation", "gnta"),
    ),
    PricingEntry(
        nom_fr="Bordures béton T2",
        unite="ml",
        prix_min_eur=18.0,
        prix_max_eur=40.0,
        prix_moyen_eur=28.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("bordure", "béton", "t2", "caniveau", "trottoir"),
    ),
    PricingEntry(
        nom_fr="Trottoir dallé / pavé",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("trottoir", "dalle", "pavé", "piéton", "cheminement"),
    ),
    PricingEntry(
        nom_fr="Réseau assainissement — canalisation PVC DN200",
        unite="ml",
        prix_min_eur=45.0,
        prix_max_eur=120.0,
        prix_moyen_eur=75.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("assainissement", "canalisation", "pvc", "réseau", "eaux usées", "eaux pluviales"),
    ),
    PricingEntry(
        nom_fr="Réseau assainissement — regard béton",
        unite="U",
        prix_min_eur=400.0,
        prix_max_eur=1200.0,
        prix_moyen_eur=700.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("assainissement", "regard", "béton", "boîte", "branchement"),
    ),
    PricingEntry(
        nom_fr="Réseau eau potable (PE/PEHD DN63)",
        unite="ml",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("eau potable", "aep", "pehd", "réseau", "adduction"),
    ),
    PricingEntry(
        nom_fr="Éclairage public — mât + luminaire LED",
        unite="U",
        prix_min_eur=2000.0,
        prix_max_eur=5000.0,
        prix_moyen_eur=3200.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("éclairage", "public", "mât", "candélabre", "luminaire", "led"),
    ),
    PricingEntry(
        nom_fr="Tranchée pour réseaux secs / humides",
        unite="ml",
        prix_min_eur=20.0,
        prix_max_eur=60.0,
        prix_moyen_eur=38.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("tranchée", "réseau", "sec", "humide", "gaine", "fourreau"),
    ),
    PricingEntry(
        nom_fr="Espace vert — engazonnement",
        unite="m2",
        prix_min_eur=5.0,
        prix_max_eur=15.0,
        prix_moyen_eur=9.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("espace vert", "gazon", "engazonnement", "pelouse", "semis"),
    ),
    PricingEntry(
        nom_fr="Espace vert — plantation arbre tige",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=800.0,
        prix_moyen_eur=450.0,
        source="Batiprix 2024",
        categorie="VRD",
        keywords=("espace vert", "arbre", "plantation", "tige", "végétal"),
    ),
    PricingEntry(
        nom_fr="Clôture grillagée (hauteur 2m)",
        unite="ml",
        prix_min_eur=40.0,
        prix_max_eur=100.0,
        prix_moyen_eur=65.0,
        source="Batiprix 2024",
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
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "chaudière", "gaz", "condensation", "chauffage"),
    ),
    PricingEntry(
        nom_fr="CVC — pompe à chaleur air/eau",
        unite="U",
        prix_min_eur=8000.0,
        prix_max_eur=25000.0,
        prix_moyen_eur=15000.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "pac", "pompe", "chaleur", "air", "eau", "thermodynamique"),
    ),
    PricingEntry(
        nom_fr="CVC — radiateur acier (type 22, 1000mm)",
        unite="U",
        prix_min_eur=150.0,
        prix_max_eur=400.0,
        prix_moyen_eur=250.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "radiateur", "acier", "chauffage", "émetteur"),
    ),
    PricingEntry(
        nom_fr="CVC — plancher chauffant hydraulique",
        unite="m2",
        prix_min_eur=40.0,
        prix_max_eur=90.0,
        prix_moyen_eur=60.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "plancher", "chauffant", "hydraulique", "sol"),
    ),
    PricingEntry(
        nom_fr="CVC — gaine de ventilation tôle galvanisée",
        unite="ml",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "ventilation", "gaine", "vmc", "tôle", "galvanisée"),
    ),
    PricingEntry(
        nom_fr="CVC — CTA (Centrale de Traitement d'Air)",
        unite="U",
        prix_min_eur=5000.0,
        prix_max_eur=30000.0,
        prix_moyen_eur=15000.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "cta", "centrale", "traitement", "air", "climatisation"),
    ),
    PricingEntry(
        nom_fr="CVC — split / climatiseur mono-split",
        unite="U",
        prix_min_eur=1200.0,
        prix_max_eur=3500.0,
        prix_moyen_eur=2200.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("cvc", "split", "climatiseur", "clim", "froid"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — WC complet (pose)",
        unite="U",
        prix_min_eur=350.0,
        prix_max_eur=900.0,
        prix_moyen_eur=550.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("plomberie", "wc", "toilette", "sanitaire", "cuvette"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — douche complète (receveur + robinetterie + paroi)",
        unite="U",
        prix_min_eur=800.0,
        prix_max_eur=2500.0,
        prix_moyen_eur=1400.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("plomberie", "douche", "receveur", "bac", "robinetterie"),
    ),
    PricingEntry(
        nom_fr="Plomberie sanitaire — chauffe-eau thermodynamique",
        unite="U",
        prix_min_eur=2000.0,
        prix_max_eur=5000.0,
        prix_moyen_eur=3200.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("plomberie", "chauffe-eau", "ballon", "ecs", "thermodynamique"),
    ),
    PricingEntry(
        nom_fr="Courants forts — câblage VDI (prise RJ45)",
        unite="U",
        prix_min_eur=80.0,
        prix_max_eur=200.0,
        prix_moyen_eur=130.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("courant", "faible", "vdi", "rj45", "réseau", "informatique"),
    ),
    PricingEntry(
        nom_fr="Courants forts — chemin de câbles",
        unite="ml",
        prix_min_eur=15.0,
        prix_max_eur=45.0,
        prix_moyen_eur=28.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("courant", "chemin", "câble", "goulotte", "électrique"),
    ),
    PricingEntry(
        nom_fr="Sécurité incendie — détecteur (DAI)",
        unite="U",
        prix_min_eur=60.0,
        prix_max_eur=200.0,
        prix_moyen_eur=120.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("incendie", "détecteur", "dai", "ssi", "alarme", "sécurité"),
    ),
    PricingEntry(
        nom_fr="Sécurité incendie — extincteur ABC",
        unite="U",
        prix_min_eur=30.0,
        prix_max_eur=80.0,
        prix_moyen_eur=50.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("incendie", "extincteur", "abc", "sécurité"),
    ),
    PricingEntry(
        nom_fr="Ascenseur (cabine standard, 8 personnes, 5 niveaux)",
        unite="U",
        prix_min_eur=35000.0,
        prix_max_eur=80000.0,
        prix_moyen_eur=55000.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("ascenseur", "élévateur", "monte-charge", "cabine"),
    ),
    PricingEntry(
        nom_fr="Photovoltaïque — panneau solaire (pose sur toiture)",
        unite="Wc",
        prix_min_eur=1.5,
        prix_max_eur=3.0,
        prix_moyen_eur=2.2,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("photovoltaïque", "solaire", "panneau", "pv", "wc"),
    ),
    PricingEntry(
        nom_fr="GTB / GTC — point de comptage / mesure",
        unite="U",
        prix_min_eur=200.0,
        prix_max_eur=600.0,
        prix_moyen_eur=380.0,
        source="Batiprix 2024",
        categorie="Lot technique",
        keywords=("gtb", "gtc", "gestion", "technique", "bâtiment", "automate"),
    ),
]

# ── Référentiel consolidé ───────────────────────────────────────────────────

PRICING_REFERENCE: list[PricingEntry] = GROS_OEUVRE + SECOND_OEUVRE + VRD + LOT_TECHNIQUE

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
    for score, entry in scored[:10]:  # Max 10 résultats
        results.append({
            "nom_fr": entry.nom_fr,
            "unite": entry.unite,
            "prix_min_eur": entry.prix_min_eur,
            "prix_max_eur": entry.prix_max_eur,
            "prix_moyen_eur": entry.prix_moyen_eur,
            "source": entry.source,
            "categorie": entry.categorie,
            "relevance_score": round(score, 2),
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


def check_dpgf_pricing(rows: list[dict]) -> list[dict[str, Any]]:
    """Compare chaque ligne DPGF au référentiel et signale les anomalies.

    Args:
        rows: Liste de dictionnaires représentant les lignes DPGF. Chaque dict
            doit contenir au minimum :
            - designation (str) : description du poste
            - prix_unitaire (str|float) : prix unitaire HT
            Optionnels : unite (str), quantite (str|float), montant_ht (str|float)

    Returns:
        Liste de dictionnaires, un par ligne, avec :
        - designation : str -- désignation originale
        - prix_unitaire : float|None -- prix unitaire de la ligne DPGF
        - reference_match : str|None -- nom du poste de référence le plus proche
        - reference_unite : str|None -- unité de référence
        - reference_prix_min : float|None -- prix min référentiel
        - reference_prix_max : float|None -- prix max référentiel
        - reference_prix_moyen : float|None -- prix moyen référentiel
        - status : str -- "SOUS_EVALUE" | "NORMAL" | "SUR_EVALUE" | "INCONNU"
        - ratio_vs_moyen : float|None -- ratio prix DPGF / prix moyen référentiel
            (ex: 0.6 = 40% sous la moyenne, 1.5 = 50% au-dessus)
        - alerte : str -- message d'alerte lisible (vide si NORMAL ou INCONNU)
        - categorie : str|None -- catégorie BTP du poste de référence
    """
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
            })
            continue

        # Calculer le ratio vs prix moyen
        ratio = round(prix_unitaire / match.prix_moyen_eur, 2) if match.prix_moyen_eur > 0 else None

        # Déterminer le statut
        if prix_unitaire < match.prix_min_eur:
            status = "SOUS_EVALUE"
            ecart_pct = round((1 - prix_unitaire / match.prix_min_eur) * 100)
            alerte = (
                f"Prix unitaire ({prix_unitaire:.2f} EUR/{match.unite}) inférieur "
                f"au minimum référentiel ({match.prix_min_eur:.2f} EUR/{match.unite}). "
                f"Écart : -{ecart_pct}% sous le plancher."
            )
        elif prix_unitaire > match.prix_max_eur:
            status = "SUR_EVALUE"
            ecart_pct = round((prix_unitaire / match.prix_max_eur - 1) * 100)
            alerte = (
                f"Prix unitaire ({prix_unitaire:.2f} EUR/{match.unite}) supérieur "
                f"au maximum référentiel ({match.prix_max_eur:.2f} EUR/{match.unite}). "
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
            "reference_prix_min": match.prix_min_eur,
            "reference_prix_max": match.prix_max_eur,
            "reference_prix_moyen": match.prix_moyen_eur,
            "status": status,
            "ratio_vs_moyen": ratio,
            "alerte": alerte,
            "categorie": match.categorie,
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
        "source": "Batiprix / indices BTP publics (indicatif)",
        "year": 2024,
    }
