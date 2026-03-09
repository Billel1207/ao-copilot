"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("plan", sa.String(20), default="starter"),
        sa.Column("quota_docs", sa.Integer, default=20),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_pw", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), default="member"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ao_projects
    op.create_table(
        "ao_projects",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("buyer", sa.String(255), nullable=True),
        sa.Column("market_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("submission_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ao_documents
    op.create_table(
        "ao_documents",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("doc_type", sa.String(20), nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("file_size_kb", sa.Integer, nullable=True),
        sa.Column("has_text", sa.Boolean, default=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # document_pages
    op.create_table(
        "document_pages",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("ao_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_num", sa.Integer, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("char_count", sa.Integer, nullable=True),
        sa.Column("section", sa.String(255), nullable=True),
    )

    # chunks
    op.create_table(
        "chunks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("ao_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("page_start", sa.Integer, nullable=True),
        sa.Column("page_end", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("embedding", sa.JSON, nullable=True),  # float[] stored as JSON
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    # extraction_results
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result_type", sa.String(30), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # checklist_items
    op.create_table(
        "checklist_items",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("requirement", sa.Text, nullable=False),
        sa.Column("criticality", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), default="MANQUANT"),
        sa.Column("what_to_provide", sa.Text, nullable=True),
        sa.Column("citations", sa.JSON, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("assigned_to", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # criteria_items
    op.create_table(
        "criteria_items",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=True),
        sa.Column("criterion", sa.Text, nullable=False),
        sa.Column("weight_pct", sa.Float, nullable=True),
        sa.Column("condition_type", sa.String(10), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("citations", sa.JSON, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
    )

    # access_logs
    op.create_table(
        "access_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("resource", sa.String(500), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("ua", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("access_logs")
    op.drop_table("criteria_items")
    op.drop_table("checklist_items")
    op.drop_table("extraction_results")
    op.drop_table("chunks")
    op.drop_table("document_pages")
    op.drop_table("ao_documents")
    op.drop_table("ao_projects")
    op.drop_table("users")
    op.drop_table("organizations")
