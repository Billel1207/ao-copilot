"""011 — Monitoring TED : colonne source sur ao_watch_results + ted_enabled sur ao_watch_configs

Revision ID: 011
Revises: 010
Create Date: 2026-03-08

Context :
- ao_watch_results.source  (VARCHAR 20, défaut 'BOAMP') : distingue les AO BOAMP des AO TED.
- ao_watch_configs.ted_enabled (BOOLEAN, défaut false) : active la veille TED par org.
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Colonne source sur les résultats de veille
    op.add_column(
        "ao_watch_results",
        sa.Column("source", sa.String(20), server_default="BOAMP", nullable=False),
    )

    # Flag d'activation du monitoring TED par organisation
    op.add_column(
        "ao_watch_configs",
        sa.Column("ted_enabled", sa.Boolean(), server_default="false", nullable=False),
    )

    # Index pour filtrer rapidement par source (BOAMP vs TED)
    op.create_index(
        "idx_watch_results_source",
        "ao_watch_results",
        ["source"],
    )


def downgrade() -> None:
    op.drop_index("idx_watch_results_source", table_name="ao_watch_results")
    op.drop_column("ao_watch_configs", "ted_enabled")
    op.drop_column("ao_watch_results", "source")
