"""Thème visuel centralisé pour les exports PDF et DOCX d'AO Copilot.

Toutes les couleurs, polices et espacements des rapports sont définis ici.
Modifier ce fichier suffit pour changer l'apparence de tous les exports.

White-labeling (plan Business) : `get_theme(org_id=...)` fusionne
les surcharges du `custom_theme` JSON de CompanyProfile avec DEFAULT_THEME.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional


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

# Champs autorisés pour la surcharge custom_theme (sécurité : pas de font_family)
_ALLOWED_THEME_KEYS = {f.name for f in fields(ReportTheme) if "color" in f.name or f.name.endswith("_bg") or f.name.endswith("_text") or f.name == "primary" or f.name == "primary_dark" or f.name == "header_bg"}

# Cache per-org pour éviter des queries répétées dans un même export
_theme_cache: dict[str, ReportTheme] = {}


def get_theme(org_id: Optional[str] = None) -> ReportTheme:
    """Retourne le thème actif, avec surcharges per-org pour le plan Business.

    Args:
        org_id: UUID de l'organisation (optionnel). Si fourni, cherche
                un custom_theme dans CompanyProfile.

    Returns:
        ReportTheme (DEFAULT_THEME si pas de surcharge ou org_id absent)
    """
    if not org_id:
        return DEFAULT_THEME

    # Cache hit
    if org_id in _theme_cache:
        return _theme_cache[org_id]

    try:
        from app.core.database import SyncSessionLocal
        from app.models.company_profile import CompanyProfile

        db = SyncSessionLocal()
        try:
            import uuid
            profile = db.query(CompanyProfile).filter_by(
                org_id=uuid.UUID(org_id)
            ).first()

            if not profile or not profile.custom_theme or not isinstance(profile.custom_theme, dict):
                _theme_cache[org_id] = DEFAULT_THEME
                return DEFAULT_THEME

            # Merge only allowed keys (prevent injection of font_family or other fields)
            overrides = {
                k: v for k, v in profile.custom_theme.items()
                if k in _ALLOWED_THEME_KEYS and isinstance(v, str) and v.startswith("#") and len(v) <= 9
            }

            if not overrides:
                _theme_cache[org_id] = DEFAULT_THEME
                return DEFAULT_THEME

            # Create theme with overrides
            import dataclasses
            theme = dataclasses.replace(DEFAULT_THEME, **overrides)
            _theme_cache[org_id] = theme
            return theme
        finally:
            db.close()

    except Exception:
        # Any error → fallback to default (non-critical feature)
        return DEFAULT_THEME
