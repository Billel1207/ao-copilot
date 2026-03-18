"""Thème visuel centralisé pour les exports PDF et DOCX d'AO Copilot.

Toutes les couleurs, polices et espacements des rapports sont définis ici.
Modifier ce fichier suffit pour changer l'apparence de tous les exports.
"""
from dataclasses import dataclass, field


@dataclass
class ReportTheme:
    """Palette et typographie pour les rapports AO Copilot."""

    # Couleurs primaires
    primary: str = "#2563EB"       # Bleu Copilot (titres, liens, badges)
    primary_dark: str = "#1D4ED8"  # Bleu foncé (hover, accents)
    header_bg: str = "#0F1B4C"     # En-tête tables (bleu nuit)
    header_text: str = "#FFFFFF"   # Texte sur fond foncé

    # Sémantique risques / statuts
    risk_high_bg: str = "#FDE8E8"   # Fond rouge pâle
    risk_high_text: str = "#B91C1C"  # Texte rouge foncé
    risk_med_bg: str = "#FEF3C7"    # Fond orange pâle
    risk_med_text: str = "#B45309"   # Texte orange foncé
    risk_low_bg: str = "#ECFDF5"    # Fond vert pâle
    risk_low_text: str = "#059669"   # Texte vert foncé
    info_bg: str = "#EFF6FF"         # Fond bleu pâle (infos)
    info_text: str = "#1D4ED8"       # Texte bleu

    # Neutres
    neutral_bg: str = "#F1F5F9"      # Fond lignes alternées
    border_color: str = "#E2E8F0"    # Bordures tables
    text_primary: str = "#1A1A2E"    # Corps texte
    text_secondary: str = "#475569"  # Texte secondaire
    text_muted: str = "#94A3B8"      # Texte discret (footer, dates)

    # Go / No-Go
    go_bg: str = "#D1FAE5"
    go_text: str = "#065F46"
    nogo_bg: str = "#FEE2E2"
    nogo_text: str = "#991B1B"
    conditional_bg: str = "#FEF9C3"
    conditional_text: str = "#92400E"

    # Typographie
    font_family: str = "'Helvetica Neue', Helvetica, Arial, sans-serif"
    font_size_body: str = "11px"
    font_size_small: str = "9px"
    font_size_h1: str = "20px"
    font_size_h2: str = "14px"
    font_size_h3: str = "12px"
    line_height: str = "1.55"


# Instance par défaut utilisée par tous les exports
DEFAULT_THEME = ReportTheme()


def get_theme() -> ReportTheme:
    """Retourne le thème actif (extensible : thème client personnalisé futur)."""
    return DEFAULT_THEME
