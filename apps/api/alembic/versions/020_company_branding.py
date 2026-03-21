"""020 — Add white-labeling fields to company_profiles.

Adds logo_s3_key and custom_theme for Business plan white-labeling.
Custom theme allows per-org color overrides in PDF/DOCX/Excel exports.

Revision ID: 020
Revises: 019
"""
from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "company_profiles",
        sa.Column("logo_s3_key", sa.String(512), nullable=True),
    )
    op.add_column(
        "company_profiles",
        sa.Column("custom_theme", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("company_profiles", "custom_theme")
    op.drop_column("company_profiles", "logo_s3_key")
