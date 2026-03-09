import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AoWatchConfig(Base):
    __tablename__ = "ao_watch_configs"
    __table_args__ = (
        UniqueConstraint("org_id", name="uq_ao_watch_configs_org_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    regions: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    cpv_codes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    min_budget_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_budget_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ted_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization")


class AoWatchResult(Base):
    __tablename__ = "ao_watch_results"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="BOAMP", server_default="BOAMP")
    boamp_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    buyer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_value_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    procedure: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cpv_codes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization")
