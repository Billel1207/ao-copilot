"""008 — Ajout colonne trial_expires_at sur organizations + plan trial

Revision ID: 008
Revises: 007
Create Date: 2026-03-08

Context : Support du plan d'essai 14 jours.
Ajoute la colonne trial_expires_at (nullable) sur la table organizations.
Les nouvelles inscriptions reçoivent plan='trial' et trial_expires_at = NOW() + 14 jours.
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organizations", "trial_expires_at")
