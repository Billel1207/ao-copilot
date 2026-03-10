"""Simulateur de trésorerie (cash-flow) pour marchés publics BTP.

Calcul déterministe (pas de LLM) du Besoin en Fonds de Roulement (BFR),
de la courbe de trésorerie mensuelle et des mois critiques.

Alimenté par les données extraites de l'Acte d'Engagement et du CCAP :
avance forfaitaire, retenue de garantie, délai de paiement, pénalités,
durée du marché, montant total.

Références :
- CCAG-Travaux 2021 Art. 14.1 (avance), 14.3 (retenue), 11.6 (paiement 30j)
- Art. R2191-3 CCP (avance obligatoire si > 50k€ HT et durée > 2 mois)
"""
import math
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CashFlowMonth:
    """Flux de trésorerie d'un mois."""
    mois: int                    # Numéro du mois (1-based)
    travaux_realises_ht: float   # CA réalisé dans le mois
    depenses_ht: float           # Dépenses engagées (matériaux, MO, sous-traitants)
    encaissement_ht: float       # Encaissements reçus (avec décalage paiement)
    solde_mensuel: float         # Encaissements - Dépenses
    solde_cumule: float          # Trésorerie cumulée


def simulate_cashflow(
    montant_total_ht: float,
    duree_mois: int,
    avance_pct: float = 5.0,
    retenue_pct: float = 5.0,
    delai_paiement_jours: int = 30,
    penalites_jour_ratio: float = 1 / 3000,
    marge_brute_pct: float = 15.0,
    repartition: Literal["lineaire", "front_loaded", "back_loaded"] = "lineaire",
) -> dict:
    """Simule la trésorerie d'un marché public BTP sur toute sa durée.

    Args:
        montant_total_ht: Montant total du marché en € HT.
        duree_mois: Durée du marché en mois.
        avance_pct: Pourcentage d'avance forfaitaire (CCAG Art. 14.1, std 5%).
        retenue_pct: Pourcentage de retenue de garantie (CCAG Art. 14.3, max 5%).
        delai_paiement_jours: Délai de paiement en jours (CCAG Art. 11.6, std 30j).
        penalites_jour_ratio: Ratio pénalités/jour (CCAG Art. 19.1, std 1/3000).
        marge_brute_pct: Marge brute estimée (ratio charges/CA).
        repartition: Profil de production ("lineaire", "front_loaded", "back_loaded").

    Returns:
        Dict avec monthly_cashflow, bfr_eur, peak_negative_cash, tension_months,
        risk_level, avance_impact_eur, retenue_impact_eur, resume.
    """
    if montant_total_ht <= 0 or duree_mois <= 0:
        return _empty_result("Montant ou durée invalide")

    duree_mois = max(1, min(120, duree_mois))  # Clamp 1-120 mois
    avance_pct = max(0, min(30, avance_pct))
    retenue_pct = max(0, min(10, retenue_pct))
    marge_brute_pct = max(0, min(50, marge_brute_pct))
    delai_paiement_jours = max(0, min(90, delai_paiement_jours))
    delai_paiement_mois = math.ceil(delai_paiement_jours / 30)

    # ── 1. Répartition de la production mensuelle ───────────────────────

    weights = _compute_production_weights(duree_mois, repartition)
    travaux_mensuels = [montant_total_ht * w for w in weights]

    # ── 2. Calcul de l'avance ────────────────────────────────────────────

    avance_ht = montant_total_ht * (avance_pct / 100)
    # L'avance est remboursée progressivement (déduction 1/N sur chaque situation)
    remboursement_avance_mensuel = avance_ht / max(duree_mois, 1) if avance_ht > 0 else 0

    # ── 3. Retenue de garantie ───────────────────────────────────────────

    retenue_ratio = retenue_pct / 100

    # ── 4. Simulation mois par mois ──────────────────────────────────────

    monthly: list[dict] = []
    solde_cumule = 0.0
    ratio_depenses = 1.0 - (marge_brute_pct / 100)  # Part des dépenses dans le CA

    # Mois 0 : réception de l'avance (avant démarrage des travaux)
    if avance_ht > 0:
        solde_cumule += avance_ht
        monthly.append({
            "mois": 0,
            "label": "Avance forfaitaire",
            "travaux_realises_ht": 0,
            "depenses_ht": 0,
            "encaissement_ht": round(avance_ht, 2),
            "solde_mensuel": round(avance_ht, 2),
            "solde_cumule": round(solde_cumule, 2),
        })

    # Buffer des situations à encaisser (FIFO avec décalage)
    encaissements_futurs: list[tuple[int, float]] = []  # (mois_encaissement, montant)

    for m in range(1, duree_mois + 1):
        travaux_m = travaux_mensuels[m - 1]

        # Dépenses du mois (immédiates)
        depenses_m = travaux_m * ratio_depenses

        # Situation du mois = travaux réalisés - retenue - remboursement avance
        situation_nette = travaux_m * (1 - retenue_ratio) - remboursement_avance_mensuel
        situation_nette = max(0, situation_nette)

        # L'encaissement arrive avec un décalage de delai_paiement_mois
        mois_encaissement = m + delai_paiement_mois
        encaissements_futurs.append((mois_encaissement, situation_nette))

        # Encaissements reçus ce mois-ci
        encaissement_m = sum(
            montant for mois_enc, montant in encaissements_futurs
            if mois_enc == m
        )

        solde_mensuel = encaissement_m - depenses_m
        solde_cumule += solde_mensuel

        monthly.append({
            "mois": m,
            "label": f"Mois {m}",
            "travaux_realises_ht": round(travaux_m, 2),
            "depenses_ht": round(depenses_m, 2),
            "encaissement_ht": round(encaissement_m, 2),
            "solde_mensuel": round(solde_mensuel, 2),
            "solde_cumule": round(solde_cumule, 2),
        })

    # Mois post-chantier : encaissements restants + libération retenue
    mois_post = duree_mois + 1
    while mois_post <= duree_mois + delai_paiement_mois + 2:
        encaissement_m = sum(
            montant for mois_enc, montant in encaissements_futurs
            if mois_enc == mois_post
        )
        if encaissement_m <= 0 and mois_post > duree_mois + delai_paiement_mois:
            break

        solde_mensuel = encaissement_m
        solde_cumule += solde_mensuel

        monthly.append({
            "mois": mois_post,
            "label": f"Post-chantier M+{mois_post - duree_mois}",
            "travaux_realises_ht": 0,
            "depenses_ht": 0,
            "encaissement_ht": round(encaissement_m, 2),
            "solde_mensuel": round(solde_mensuel, 2),
            "solde_cumule": round(solde_cumule, 2),
        })
        mois_post += 1

    # Libération retenue de garantie (12 mois après réception — GPA)
    retenue_totale = montant_total_ht * retenue_ratio
    if retenue_totale > 0:
        mois_liberation = duree_mois + 12  # Après la GPA de 1 an
        solde_cumule += retenue_totale
        monthly.append({
            "mois": mois_liberation,
            "label": "Libération retenue garantie (GPA)",
            "travaux_realises_ht": 0,
            "depenses_ht": 0,
            "encaissement_ht": round(retenue_totale, 2),
            "solde_mensuel": round(retenue_totale, 2),
            "solde_cumule": round(solde_cumule, 2),
        })

    # ── 5. Calcul des indicateurs ────────────────────────────────────────

    soldes_cumules = [m["solde_cumule"] for m in monthly]
    peak_negative = min(soldes_cumules) if soldes_cumules else 0
    tension_months = [m["mois"] for m in monthly if m["solde_cumule"] < 0]

    # BFR = creux max de trésorerie (en valeur absolue)
    bfr = abs(peak_negative) if peak_negative < 0 else 0

    # Impact des paramètres financiers
    avance_impact = avance_ht
    retenue_impact = retenue_totale
    penalite_impact_30j = montant_total_ht * penalites_jour_ratio * 30  # Impact 1 mois retard

    # Risk level
    if bfr > montant_total_ht * 0.20 or len(tension_months) > duree_mois * 0.5:
        risk_level = "CRITIQUE"
    elif bfr > montant_total_ht * 0.10 or len(tension_months) > duree_mois * 0.3:
        risk_level = "ÉLEVÉ"
    elif bfr > montant_total_ht * 0.05 or len(tension_months) > 2:
        risk_level = "MODÉRÉ"
    else:
        risk_level = "FAIBLE"

    # ── 6. Résumé textuel ────────────────────────────────────────────────

    resume_parts = [
        f"Marché de {montant_total_ht:,.0f} € HT sur {duree_mois} mois.",
    ]
    if avance_ht > 0:
        resume_parts.append(f"Avance de {avance_pct}% ({avance_ht:,.0f} €) reçue au démarrage.")
    if retenue_totale > 0:
        resume_parts.append(f"Retenue de {retenue_pct}% ({retenue_totale:,.0f} €) libérée après GPA.")
    if bfr > 0:
        resume_parts.append(f"BFR estimé : {bfr:,.0f} €. {len(tension_months)} mois en trésorerie négative.")
    else:
        resume_parts.append("Trésorerie positive tout au long du chantier.")
    resume_parts.append(f"Risque trésorerie : {risk_level}.")

    return {
        "monthly_cashflow": monthly,
        "bfr_eur": round(bfr, 2),
        "peak_negative_cash": round(peak_negative, 2),
        "tension_months": tension_months,
        "nb_tension_months": len(tension_months),
        "risk_level": risk_level,
        "avance_impact_eur": round(avance_impact, 2),
        "retenue_impact_eur": round(retenue_impact, 2),
        "penalite_impact_30j_eur": round(penalite_impact_30j, 2),
        "montant_total_ht": round(montant_total_ht, 2),
        "duree_mois": duree_mois,
        "marge_brute_pct": marge_brute_pct,
        "resume": " ".join(resume_parts),
    }


def _compute_production_weights(
    duree: int, repartition: str
) -> list[float]:
    """Calcule les poids de production mensuelle selon le profil choisi.

    Returns:
        Liste de poids normalisés (somme = 1.0).
    """
    if repartition == "front_loaded":
        # Plus de travaux en début de chantier
        raw = [max(0.5, 1.0 - (i / duree) * 0.6) for i in range(duree)]
    elif repartition == "back_loaded":
        # Plus de travaux en fin de chantier
        raw = [max(0.5, 0.4 + (i / duree) * 0.6) for i in range(duree)]
    else:
        # Linéaire — répartition uniforme
        raw = [1.0] * duree

    total = sum(raw)
    return [w / total for w in raw]


def _empty_result(reason: str) -> dict:
    """Retourne un résultat vide."""
    return {
        "monthly_cashflow": [],
        "bfr_eur": 0,
        "peak_negative_cash": 0,
        "tension_months": [],
        "nb_tension_months": 0,
        "risk_level": "INCONNU",
        "avance_impact_eur": 0,
        "retenue_impact_eur": 0,
        "penalite_impact_30j_eur": 0,
        "montant_total_ht": 0,
        "duree_mois": 0,
        "marge_brute_pct": 0,
        "resume": reason,
    }
