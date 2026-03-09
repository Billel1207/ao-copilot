"""Billing tables — Subscription, Invoice, UsageRecord

Revision ID: 003
Revises: 002
Create Date: 2026-03-06

Ajoute les tables de facturation Stripe :
- subscriptions : abonnement Stripe par organisation
- invoices : factures liées aux abonnements
- usage_records : utilisation mensuelle par organisation
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── subscriptions ────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("plan", sa.String(50), server_default="free", nullable=False),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])

    # ── invoices ─────────────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=False),
        sa.Column("amount_eur", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("invoice_pdf_url", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_invoice_id"),
    )

    # ── usage_records ────────────────────────────────────────────────────────
    op.create_table(
        "usage_records",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("docs_uploaded", sa.Integer(), server_default="0", nullable=False),
        sa.Column("docs_analyzed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("api_calls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_records_org_id", "usage_records", ["org_id"])
    op.create_index(
        "ix_usage_records_org_period",
        "usage_records",
        ["org_id", "period_year", "period_month"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("usage_records")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
