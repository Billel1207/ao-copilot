"""017 — Activate pgvector extension + create IVFFlat index on chunks.embedding.

Revision ID: 017
Revises: 016
"""
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (pgvector/pgvector:pg16 image has it pre-installed)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Cast JSONB embedding column to native vector type for pgvector operators
    # Step 1: Add a native vector column
    op.execute(
        "ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_vec vector(1536)"
    )

    # Step 2: Populate from existing JSONB embeddings (if any)
    op.execute("""
        UPDATE chunks
        SET embedding_vec = embedding::text::vector
        WHERE embedding IS NOT NULL
          AND embedding_vec IS NULL
    """)

    # Step 3: Create IVFFlat index for fast cosine search
    # lists = sqrt(n_rows) is a good default; 100 lists handles up to ~10k chunks well
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_vec_cosine
        ON chunks
        USING ivfflat (embedding_vec vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_vec_cosine")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding_vec")
