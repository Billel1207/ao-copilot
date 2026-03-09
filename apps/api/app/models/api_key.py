"""Modèle de clés API pour l'accès programmatique à l'API publique AO Copilot."""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Mon ERP", "Intégration Acumatica"
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # "aoc_" + 6 chars
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # SHA-256 hash de la clé complète

    # Permissions (scope)
    can_read_projects: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    can_write_projects: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    can_read_analysis: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    can_trigger_analysis: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, server_default=text("60"))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
