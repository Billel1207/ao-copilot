"""016 — Ajout des colonnes SSO SAML sur organizations (plan Business).

Revision ID: 016
Revises: 015
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("organizations", sa.Column("sso_idp_entity_id", sa.String(500), nullable=True))
    op.add_column("organizations", sa.Column("sso_idp_sso_url", sa.String(500), nullable=True))
    op.add_column("organizations", sa.Column("sso_idp_certificate", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("sso_idp_slo_url", sa.String(500), nullable=True))


def downgrade():
    op.drop_column("organizations", "sso_idp_slo_url")
    op.drop_column("organizations", "sso_idp_certificate")
    op.drop_column("organizations", "sso_idp_sso_url")
    op.drop_column("organizations", "sso_idp_entity_id")
