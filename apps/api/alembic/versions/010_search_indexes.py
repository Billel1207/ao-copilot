"""010 — Index trigrammes pg_trgm pour la recherche full-text cross-projets

Revision ID: 010
Revises: 007
Create Date: 2026-03-08

Context : Ajoute l'extension pg_trgm et des index GIN sur les colonnes
          ao_projects.title, buyer et reference pour accélérer les
          recherches ILIKE (opérateur ~~ via GIN gin_trgm_ops).
"""
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Activer l'extension pg_trgm (nécessaire pour les index GIN trigrammes)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Index GIN sur le titre du projet
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_proj_title_trgm "
        "ON ao_projects USING gin(title gin_trgm_ops)"
    )

    # Index GIN sur l'acheteur
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_proj_buyer_trgm "
        "ON ao_projects USING gin(buyer gin_trgm_ops)"
    )

    # Index GIN sur la référence
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_proj_reference_trgm "
        "ON ao_projects USING gin(reference gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_proj_reference_trgm")
    op.execute("DROP INDEX IF EXISTS idx_proj_buyer_trgm")
    op.execute("DROP INDEX IF EXISTS idx_proj_title_trgm")
    # Ne pas supprimer pg_trgm — d'autres index pourraient en dépendre
