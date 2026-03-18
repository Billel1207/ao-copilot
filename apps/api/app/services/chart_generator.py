"""Génération de graphiques PNG pour les exports PDF et DOCX d'AO Copilot.

Chaque fonction retourne un BytesIO contenant un PNG prêt à embarquer.
Si matplotlib n'est pas disponible, les fonctions retournent None (dégradation gracieuse).

Usage:
    from app.services.chart_generator import generate_gonogo_radar, generate_cashflow_chart
    radar_png = generate_gonogo_radar({"Capacité financière": 72, ...})
    if radar_png:
        b64 = base64.b64encode(radar_png.getvalue()).decode()
"""
from __future__ import annotations

import base64
import math
from io import BytesIO
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# Palette AO Copilot (synchronisée avec report_theme.py)
_PRIMARY = "#2563EB"
_PRIMARY_DARK = "#0F1B4C"
_SUCCESS = "#059669"
_WARNING = "#B45309"
_DANGER = "#B91C1C"
_NEUTRAL = "#475569"
_BG = "#F8FAFC"
_GRID = "#E2E8F0"

# Dimensions Go/No-Go dans l'ordre d'affichage radar
GONOGO_DIMENSIONS_ORDER = [
    "Capacité financière",
    "Certifications & agréments",
    "Références similaires",
    "Charge actuelle",
    "Zone géographique",
    "Partenariats disponibles",
    "Marge visée",
    "Délai de réponse",
    "Risque technique global",
]

# Labels courts pour le radar (évite les coupures)
GONOGO_LABELS_SHORT = {
    "Capacité financière": "Financier",
    "Certifications & agréments": "Certif.",
    "Références similaires": "Références",
    "Charge actuelle": "Charge",
    "Zone géographique": "Zone géo",
    "Partenariats disponibles": "Partenariats",
    "Marge visée": "Marge",
    "Délai de réponse": "Délai",
    "Risque technique global": "Risque tech.",
}


def _get_matplotlib():
    """Import conditionnel matplotlib — retourne le module ou None."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # backend non-interactif obligatoire en server
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        return plt, mpatches
    except ImportError:
        logger.warning("matplotlib_not_available", message="Charts désactivés — pip install matplotlib")
        return None, None


def generate_gonogo_radar(
    dimensions: dict[str, float],
    score_global: Optional[int] = None,
    title: str = "Score Go/No-Go",
) -> Optional[BytesIO]:
    """Graphique radar pour les 9 dimensions Go/No-Go.

    Args:
        dimensions: Dict {nom_dimension: score_0_100}
        score_global: Score global /100 (affiché au centre)
        title: Titre du graphique

    Returns:
        BytesIO PNG ou None si matplotlib absent
    """
    plt, mpatches = _get_matplotlib()
    if plt is None:
        return None

    try:
        # Normaliser les clés (insensible à la casse, aliases)
        _aliases = {
            "capacite_financiere": "Capacité financière",
            "certifications": "Certifications & agréments",
            "references_btp": "Références similaires",
            "charge_actuelle": "Charge actuelle",
            "zone_geo": "Zone géographique",
            "partenariats": "Partenariats disponibles",
            "marge_visee": "Marge visée",
            "delai_reponse": "Délai de réponse",
            "risque_technique": "Risque technique global",
        }
        normalized: dict[str, float] = {}
        for k, v in dimensions.items():
            canonical = _aliases.get(k.lower().replace(" ", "_"), k)
            normalized[canonical] = float(v)

        # Construire la liste dans l'ordre défini
        labels = []
        values = []
        for dim in GONOGO_DIMENSIONS_ORDER:
            val = normalized.get(dim, 0.0)
            labels.append(GONOGO_LABELS_SHORT.get(dim, dim))
            values.append(min(100.0, max(0.0, val)))

        if not values:
            return None

        N = len(labels)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        values_plot = values + [values[0]]  # fermer le polygone
        angles_plot = angles + [angles[0]]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor("white")
        ax.set_facecolor(_BG)

        # Grille concentrique (0, 25, 50, 75, 100)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color=_NEUTRAL)
        ax.yaxis.set_tick_params(labelleft=True)
        ax.set_rlabel_position(0)

        # Couleur de fond par zone
        ax.fill_between(angles_plot, 0, 100, alpha=0.05, color="#94A3B8")
        ax.fill_between(angles_plot, 0, 75, alpha=0.04, color="#FCD34D")
        ax.fill_between(angles_plot, 0, 50, alpha=0.04, color="#F87171")

        # Courbe des scores
        score_avg = sum(values) / len(values) if values else 0
        if score_avg >= 70:
            color = _SUCCESS
        elif score_avg >= 50:
            color = _WARNING
        else:
            color = _DANGER

        ax.plot(angles_plot, values_plot, linewidth=2.5, linestyle="solid", color=color)
        ax.fill(angles_plot, values_plot, alpha=0.22, color=color)

        # Points sur chaque axe
        ax.scatter(angles, values, s=60, color=color, zorder=5, edgecolors="white", linewidths=1.5)

        # Labels axes
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, fontsize=8, color=_PRIMARY_DARK, fontweight="semibold")

        # Grille
        ax.grid(color=_GRID, linestyle="--", linewidth=0.8, alpha=0.8)
        ax.spines["polar"].set_color(_GRID)

        # Score au centre
        center_text = f"{score_global}/100" if score_global is not None else f"{int(score_avg)}/100"
        ax.text(0, 0, center_text, ha="center", va="center",
                fontsize=16, fontweight="bold", color=color,
                transform=ax.transData)

        # Titre
        plt.title(title, fontsize=11, fontweight="bold", color=_PRIMARY_DARK,
                  pad=20, fontfamily="sans-serif")

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error("chart_radar_error", error=str(e))
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def generate_cashflow_chart(
    cashflow: dict,
    title: str = "Simulation trésorerie prévisionnelle",
) -> Optional[BytesIO]:
    """Courbe de trésorerie mensuelle avec zones colorées.

    Args:
        cashflow: Dict avec "monthly_cashflow" (list de dicts {month, cumulative_eur, ...})
                  ou "simulation" avec la même structure
        title: Titre du graphique

    Returns:
        BytesIO PNG ou None
    """
    plt, mpatches = _get_matplotlib()
    if plt is None:
        return None

    try:
        # Extraire les données mensuelles
        monthly = (
            cashflow.get("monthly_cashflow")
            or cashflow.get("simulation", {}).get("monthly_cashflow")
            or cashflow.get("cashflow_mensuel")
            or []
        )
        if not monthly:
            return None

        months = [m.get("month", m.get("mois", i + 1)) for i, m in enumerate(monthly)]
        cumulative = [float(m.get("cumulative_eur", m.get("tresorerie_cumulee", 0))) for m in monthly]

        # Nettoyer les labels mois
        month_labels = [str(m) for m in months]

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("white")
        ax.set_facecolor(_BG)

        # Zones colorées (positif = vert, négatif = rouge)
        zeros = [0] * len(cumulative)
        pos_vals = [max(0, v) for v in cumulative]
        neg_vals = [min(0, v) for v in cumulative]
        x_range = range(len(cumulative))

        ax.fill_between(x_range, zeros, pos_vals, alpha=0.25, color=_SUCCESS, label="Trésorerie positive")
        ax.fill_between(x_range, zeros, neg_vals, alpha=0.25, color=_DANGER, label="BFR négatif")

        # Ligne principale
        ax.plot(x_range, cumulative, linewidth=2.5, color=_PRIMARY, marker="o",
                markersize=5, markerfacecolor="white", markeredgewidth=2,
                markeredgecolor=_PRIMARY, zorder=5)

        # Ligne zéro
        ax.axhline(0, color=_NEUTRAL, linewidth=1, linestyle="--", alpha=0.7)

        # Formatage axes
        ax.set_xticks(x_range)
        ax.set_xticklabels(month_labels, rotation=45 if len(months) > 6 else 0,
                           fontsize=8, color=_NEUTRAL)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k€" if abs(x) >= 1000 else f"{x:.0f}€")
        )
        ax.tick_params(axis="y", labelsize=8, labelcolor=_NEUTRAL)

        # Grille
        ax.grid(axis="y", color=_GRID, linestyle="--", linewidth=0.8, alpha=0.8)
        ax.grid(axis="x", color=_GRID, linestyle=":", linewidth=0.5, alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(_GRID)
        ax.spines["bottom"].set_color(_GRID)

        # Annotation point critique (minimum)
        if cumulative:
            min_idx = cumulative.index(min(cumulative))
            min_val = cumulative[min_idx]
            if min_val < 0:
                ax.annotate(
                    f"BFR max: {min_val/1000:.1f}k€",
                    xy=(min_idx, min_val),
                    xytext=(min_idx + 0.5, min_val * 1.15),
                    fontsize=7.5, color=_DANGER, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=_DANGER, lw=1.2),
                )

        ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
        ax.set_title(title, fontsize=11, fontweight="bold", color=_PRIMARY_DARK, pad=12)
        ax.set_xlabel("Mois", fontsize=8, color=_NEUTRAL)
        ax.set_ylabel("Trésorerie cumulée", fontsize=8, color=_NEUTRAL)

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error("chart_cashflow_error", error=str(e))
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def generate_risk_heatmap(
    conflicts: list[dict],
    title: str = "Heatmap — Conflits inter-documents",
) -> Optional[BytesIO]:
    """Heatmap des conflits par document et catégorie.

    Args:
        conflicts: Liste de dicts avec "doc_source", "doc_target", "conflict_type", "severity"
        title: Titre du graphique

    Returns:
        BytesIO PNG ou None
    """
    plt, mpatches = _get_matplotlib()
    if plt is None:
        return None

    try:
        if not conflicts:
            return None

        import numpy as np

        # Types de conflits connus
        CATEGORIES = [
            "prix", "délais", "technique", "administratif",
            "ccap_cctp", "quantités", "exigences"
        ]

        # Documents impliqués (uniques)
        docs: list[str] = []
        for c in conflicts:
            for key in ("doc_source", "document_source", "doc1", "document_a"):
                d = c.get(key, "")
                if d and d not in docs:
                    docs.append(d[:20])
                    break
        docs = docs[:8] or ["DCE"]  # max 8 documents

        # Construire la matrice
        matrix = np.zeros((len(docs), len(CATEGORIES)), dtype=int)
        for c in conflicts:
            sev = c.get("severity", c.get("niveau", "low"))
            weight = {"high": 3, "critical": 3, "medium": 2, "low": 1}.get(sev, 1)
            ctype = c.get("conflict_type", c.get("type", "")).lower()
            # Trouver la catégorie
            cat_idx = next(
                (i for i, cat in enumerate(CATEGORIES) if cat in ctype),
                len(CATEGORIES) - 1  # "exigences" par défaut
            )
            # Trouver le document
            for key in ("doc_source", "document_source", "doc1"):
                doc = c.get(key, "")[:20]
                if doc in docs:
                    matrix[docs.index(doc)][cat_idx] += weight
                    break

        fig, ax = plt.subplots(figsize=(9, max(3, len(docs) * 0.7 + 1)))
        fig.patch.set_facecolor("white")

        # Colormap personnalisée (blanc → bleu → rouge)
        import matplotlib.colors as mcolors
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "ao_heatmap",
            ["#FFFFFF", "#DBEAFE", "#FEF3C7", "#FEE2E2", "#B91C1C"],
            N=256
        )

        im = ax.imshow(matrix, cmap=cmap, aspect="auto",
                       vmin=0, vmax=max(matrix.max(), 3))

        # Labels
        ax.set_xticks(range(len(CATEGORIES)))
        ax.set_xticklabels(CATEGORIES, rotation=35, ha="right", fontsize=8, color=_NEUTRAL)
        ax.set_yticks(range(len(docs)))
        ax.set_yticklabels(docs, fontsize=8, color=_PRIMARY_DARK)

        # Valeurs dans les cellules
        for i in range(len(docs)):
            for j in range(len(CATEGORIES)):
                val = matrix[i, j]
                if val > 0:
                    ax.text(j, i, str(val), ha="center", va="center",
                            fontsize=9, fontweight="bold",
                            color="white" if val >= 3 else _PRIMARY_DARK)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
        cbar.set_label("Intensité conflits", fontsize=8, color=_NEUTRAL)
        cbar.ax.tick_params(labelsize=7)

        ax.set_title(title, fontsize=11, fontweight="bold", color=_PRIMARY_DARK, pad=12)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error("chart_heatmap_error", error=str(e))
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def generate_pricing_benchmark_bars(
    pricing: list[dict],
    title: str = "Benchmark DPGF — Prix vs Référentiel BTP",
) -> Optional[BytesIO]:
    """Graphique en barres horizontales comparant les prix DPGF au référentiel.

    Args:
        pricing: Liste de dicts avec "designation", "prix_saisi", "prix_min",
                 "prix_max", "status" (OK/SOUS_EVALUE/SUR_EVALUE)
        title: Titre du graphique

    Returns:
        BytesIO PNG ou None
    """
    plt, mpatches = _get_matplotlib()
    if plt is None:
        return None

    try:
        # Filtrer les lignes avec prix et alertes uniquement (top 12)
        alertes = [p for p in pricing if p.get("status") in ("SOUS_EVALUE", "SUR_EVALUE")]
        items = alertes[:12] if alertes else pricing[:12]
        if not items:
            return None

        labels = [str(p.get("designation", "?"))[:40] for p in items]
        prix = [float(p.get("prix_saisi", p.get("prix_unitaire", 0))) for p in items]
        prix_min = [float(p.get("prix_min", p.get("min", 0))) for p in items]
        prix_max = [float(p.get("prix_max", p.get("max", 0))) for p in items]
        statuses = [p.get("status", "OK") for p in items]

        colors = {
            "OK": _SUCCESS,
            "SOUS_EVALUE": _DANGER,
            "SUR_EVALUE": _WARNING,
        }
        bar_colors = [colors.get(s, _NEUTRAL) for s in statuses]

        fig, ax = plt.subplots(figsize=(9, max(4, len(items) * 0.55 + 1.5)))
        fig.patch.set_facecolor("white")
        ax.set_facecolor(_BG)

        y_pos = range(len(items))

        # Fourchette de référence (fond)
        for i, (mn, mx) in enumerate(zip(prix_min, prix_max)):
            if mn < mx:
                ax.barh(i, mx - mn, left=mn, height=0.5, color="#DBEAFE",
                        alpha=0.7, zorder=2, label="Fourchette marché" if i == 0 else "")

        # Prix saisi
        ax.barh(y_pos, prix, height=0.35, color=bar_colors, alpha=0.9, zorder=3)

        # Labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8, color=_PRIMARY_DARK)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x:.0f}€")
        )
        ax.tick_params(axis="x", labelsize=7.5, labelcolor=_NEUTRAL)

        # Grille
        ax.grid(axis="x", color=_GRID, linestyle="--", linewidth=0.8, alpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Légende
        legend_elements = [
            mpatches.Patch(facecolor=_SUCCESS, label="Prix OK"),
            mpatches.Patch(facecolor=_DANGER, label="Sous-évalué"),
            mpatches.Patch(facecolor=_WARNING, label="Sur-évalué"),
            mpatches.Patch(facecolor="#DBEAFE", label="Fourchette marché"),
        ]
        ax.legend(handles=legend_elements, loc="lower right", fontsize=7.5, framealpha=0.9)
        ax.set_title(title, fontsize=11, fontweight="bold", color=_PRIMARY_DARK, pad=12)
        ax.set_xlabel("Prix unitaire HT (€)", fontsize=8, color=_NEUTRAL)

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error("chart_pricing_error", error=str(e))
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def chart_to_base64(buf: Optional[BytesIO]) -> Optional[str]:
    """Convertit un BytesIO PNG en base64 string pour embedding HTML/PDF."""
    if buf is None:
        return None
    try:
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception:
        return None
