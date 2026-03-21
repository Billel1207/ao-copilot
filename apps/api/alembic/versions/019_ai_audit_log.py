"""019 — Create ai_audit_logs table for AI Act Article 50 compliance.

Tracks every LLM call with provider, model, tokens, latency, and prompt hash.
Enables cost monitoring, transparency reporting, and regulatory compliance.

Revision ID: 019
Revises: 018
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("ao_projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("cached_tokens", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("error_type", sa.String(200), nullable=True),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Indexes for common queries
    op.create_index("ix_ai_audit_logs_org_id", "ai_audit_logs", ["org_id"])
    op.create_index("ix_ai_audit_logs_user_id", "ai_audit_logs", ["user_id"])
    op.create_index("ix_ai_audit_logs_project_id", "ai_audit_logs", ["project_id"])
    op.create_index("ix_ai_audit_logs_provider", "ai_audit_logs", ["provider"])
    op.create_index("ix_ai_audit_logs_task_type", "ai_audit_logs", ["task_type"])
    op.create_index("ix_ai_audit_logs_created_at", "ai_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_audit_logs_created_at")
    op.drop_index("ix_ai_audit_logs_task_type")
    op.drop_index("ix_ai_audit_logs_provider")
    op.drop_index("ix_ai_audit_logs_project_id")
    op.drop_index("ix_ai_audit_logs_user_id")
    op.drop_index("ix_ai_audit_logs_org_id")
    op.drop_table("ai_audit_logs")
