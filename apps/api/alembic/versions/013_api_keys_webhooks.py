"""013 — API Keys et Webhooks pour l'API publique AO Copilot

Revision ID: 013
Revises: 012
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table des clés API
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("can_read_projects", sa.Boolean, server_default="true"),
        sa.Column("can_write_projects", sa.Boolean, server_default="false"),
        sa.Column("can_read_analysis", sa.Boolean, server_default="true"),
        sa.Column("can_trigger_analysis", sa.Boolean, server_default="false"),
        sa.Column("rate_limit_per_minute", sa.Integer, server_default="60"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # Table des endpoints webhook
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("events", sa.String(500), server_default="analysis.completed,project.created"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("failure_count", sa.Integer, server_default="0"),
        sa.Column("last_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_webhook_endpoints_org_id", "webhook_endpoints", ["org_id"])

    # Table des livraisons webhook
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("endpoint_id", sa.UUID, sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, server_default="false"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("attempt_number", sa.Integer, server_default="1"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_webhook_deliveries_endpoint_id", "webhook_deliveries", ["endpoint_id"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_endpoint_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhook_endpoints_org_id", table_name="webhook_endpoints")
    op.drop_table("webhook_endpoints")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_index("ix_api_keys_org_id", table_name="api_keys")
    op.drop_table("api_keys")
