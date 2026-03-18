"""018 — Add can_manage_billing and can_export columns to api_keys.

Revision ID: 018
Revises: 017
"""
from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("can_manage_billing", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "api_keys",
        sa.Column("can_export", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "can_export")
    op.drop_column("api_keys", "can_manage_billing")
