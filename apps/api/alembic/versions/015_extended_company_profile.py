"""Add extended company profile columns for Go/No-Go 9 dimensions.

Revision ID: 015
Revises: 014
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("company_profiles", sa.Column("assurance_rc_montant", sa.Integer(), nullable=True))
    op.add_column("company_profiles", sa.Column("assurance_decennale", sa.Boolean(), nullable=True))
    op.add_column("company_profiles", sa.Column("partenaires_specialites", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("company_profiles", sa.Column("marge_minimale_pct", sa.Integer(), nullable=True))
    op.add_column("company_profiles", sa.Column("max_projets_simultanes", sa.Integer(), nullable=True))
    op.add_column("company_profiles", sa.Column("projets_actifs_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("company_profiles", "projets_actifs_count")
    op.drop_column("company_profiles", "max_projets_simultanes")
    op.drop_column("company_profiles", "marge_minimale_pct")
    op.drop_column("company_profiles", "partenaires_specialites")
    op.drop_column("company_profiles", "assurance_decennale")
    op.drop_column("company_profiles", "assurance_rc_montant")
