"""Email lowercase unique index

Revision ID: 002
Revises: 001
Create Date: 2026-03-06

Force les adresses email en minuscules et ajoute un index unique
case-insensitive pour éviter les doublons (john@x.fr / JOHN@x.fr).
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Normaliser les emails existants en minuscules
    op.execute("UPDATE users SET email = lower(email)")

    # 2. Supprimer l'ancien index unique (case-sensitive) s'il existe
    op.execute("DROP INDEX IF EXISTS ix_users_email")

    # 3. Créer le nouvel index unique case-insensitive via expression LOWER()
    op.execute(
        "CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
    # Recréer l'index unique standard (case-sensitive)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
