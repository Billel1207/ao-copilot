"""007 — Fix organization defaults (plan=free, quota=3) + corriger orgs sans paiement Stripe

Revision ID: 007
Revises: 006
Create Date: 2026-03-08

Context : La migration corrige deux problèmes :
1. Le défaut de `organizations.plan` était "starter" (au lieu de "free")
2. Le défaut de `organizations.quota_docs` était 20 (au lieu de 3)
3. Les orgs existantes sans subscription Stripe active sont replacées en free/3 docs
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Corriger les server_default des colonnes
    op.alter_column(
        "organizations",
        "plan",
        server_default=sa.text("'free'"),
        existing_type=sa.String(20),
        existing_nullable=False,
    )
    op.alter_column(
        "organizations",
        "quota_docs",
        server_default=sa.text("3"),
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    # 2. Corriger les orgs existantes qui sont en "starter" sans avoir payé
    #    (pas de stripe_subscription_id dans la table subscriptions)
    op.execute(
        """
        UPDATE organizations
        SET plan = 'free',
            quota_docs = 3
        WHERE plan = 'starter'
          AND id NOT IN (
              SELECT org_id
              FROM subscriptions
              WHERE stripe_subscription_id IS NOT NULL
                AND status IN ('active', 'trialing')
          )
        """
    )


def downgrade() -> None:
    # Revert server defaults only (data changes cannot be fully reverted safely)
    op.alter_column(
        "organizations",
        "plan",
        server_default=sa.text("'starter'"),
        existing_type=sa.String(20),
        existing_nullable=False,
    )
    op.alter_column(
        "organizations",
        "quota_docs",
        server_default=sa.text("20"),
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
