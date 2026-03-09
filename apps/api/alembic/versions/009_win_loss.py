"""009 — Win/Loss tracking fields on ao_projects

Revision ID: 009
Revises: 008
Create Date: 2026-03-08

Ajoute les champs de suivi résultat d'appel d'offres :
- result       : won | lost | no_bid
- result_amount_eur : montant du marché remporté (€)
- result_date  : date du résultat
- result_notes : notes libres (500 car. max)
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ao_projects", sa.Column("result", sa.String(20), nullable=True))
    op.add_column("ao_projects", sa.Column("result_amount_eur", sa.Float, nullable=True))
    op.add_column("ao_projects", sa.Column("result_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ao_projects", sa.Column("result_notes", sa.String(500), nullable=True))

    # Index pour accélérer les requêtes analytics par résultat
    op.create_index("ix_ao_projects_result", "ao_projects", ["result"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ao_projects_result", table_name="ao_projects")
    op.drop_column("ao_projects", "result_notes")
    op.drop_column("ao_projects", "result_date")
    op.drop_column("ao_projects", "result_amount_eur")
    op.drop_column("ao_projects", "result")
