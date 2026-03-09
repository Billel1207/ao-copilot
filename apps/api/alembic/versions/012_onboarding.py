"""012 — Onboarding completed flag on organizations

Revision ID: 012
Revises: 011
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("onboarding_completed", sa.Boolean, server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("organizations", "onboarding_completed")
