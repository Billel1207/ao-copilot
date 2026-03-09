"""006 — project_deadlines, company_profiles, response_snippets,
       checklist_annotations, ao_watch_configs, ao_watch_results

Revision ID: 006
Revises: 005
Create Date: 2026-03-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── project_deadlines ────────────────────────────────────────────────────
    op.create_table(
        "project_deadlines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deadline_type", sa.String(50), nullable=False),
        sa.Column("label", sa.String(500), nullable=False),
        sa.Column("deadline_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_critical", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("citation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_project_deadlines_project_id", "project_deadlines", ["project_id"])
    op.create_index("ix_project_deadlines_deadline_date", "project_deadlines", ["deadline_date"])

    # ── company_profiles ─────────────────────────────────────────────────────
    op.create_table(
        "company_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("revenue_eur", sa.Integer, nullable=True),
        sa.Column("employee_count", sa.Integer, nullable=True),
        sa.Column("certifications", JSON, nullable=False, server_default="[]"),
        sa.Column("specialties", JSON, nullable=False, server_default="[]"),
        sa.Column("regions", JSON, nullable=False, server_default="[]"),
        sa.Column("max_market_size_eur", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", name="uq_company_profiles_org_id"),
    )

    # ── response_snippets ────────────────────────────────────────────────────
    op.create_table(
        "response_snippets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tags", JSON, nullable=False, server_default="[]"),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_response_snippets_org_id", "response_snippets", ["org_id"])
    op.create_index("ix_response_snippets_category", "response_snippets", ["category"])

    # ── checklist_annotations ────────────────────────────────────────────────
    op.create_table(
        "checklist_annotations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("checklist_item_id", UUID(as_uuid=True), sa.ForeignKey("checklist_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("content", sa.String(2000), nullable=False),
        sa.Column("annotation_type", sa.String(20), nullable=False, server_default=sa.text("'comment'")),
        sa.Column("author_name", sa.String(255), nullable=True),
        sa.Column("author_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_checklist_annotations_item_id", "checklist_annotations", ["checklist_item_id"])
    op.create_index("ix_checklist_annotations_project_id", "checklist_annotations", ["project_id"])

    # ── ao_watch_configs ─────────────────────────────────────────────────────
    op.create_table(
        "ao_watch_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("keywords", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("regions", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("cpv_codes", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("min_budget_eur", sa.Integer, nullable=True),
        sa.Column("max_budget_eur", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", name="uq_ao_watch_configs_org_id"),
    )

    # ── ao_watch_results ──────────────────────────────────────────────────────
    op.create_table(
        "ao_watch_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("boamp_ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("buyer", sa.String(500), nullable=True),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_value_eur", sa.Integer, nullable=True),
        sa.Column("procedure", sa.String(255), nullable=True),
        sa.Column("cpv_codes", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_watch_results_org_id", "ao_watch_results", ["org_id"])
    op.create_index("ix_ao_watch_results_boamp_ref", "ao_watch_results", ["boamp_ref"])
    op.create_index("ix_ao_watch_results_is_read", "ao_watch_results", ["is_read"])
    # Contrainte d'unicité pour la déduplication
    op.create_unique_constraint("uq_ao_watch_results_org_ref", "ao_watch_results", ["org_id", "boamp_ref"])


def downgrade() -> None:
    op.drop_table("ao_watch_results")
    op.drop_table("ao_watch_configs")
    op.drop_table("checklist_annotations")
    op.drop_table("response_snippets")
    op.drop_table("company_profiles")
    op.drop_table("project_deadlines")
