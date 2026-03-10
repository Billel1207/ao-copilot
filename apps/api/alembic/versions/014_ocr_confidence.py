"""014 — Ajout colonnes OCR confidence et qualité

Ajoute le scoring de qualité OCR par page et par document pour
améliorer la fiabilité des analyses sur PDFs scannés/dégradés.

Revision ID: 014
Revises: 013
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DocumentPage : confiance OCR par page (0-100)
    op.add_column(
        "document_pages",
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
    )

    # AoDocument : score OCR global + warning
    op.add_column(
        "ao_documents",
        sa.Column("ocr_quality_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "ao_documents",
        sa.Column("ocr_warning", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ao_documents", "ocr_warning")
    op.drop_column("ao_documents", "ocr_quality_score")
    op.drop_column("document_pages", "ocr_confidence")
