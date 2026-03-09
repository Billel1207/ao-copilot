import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Integer, JSON, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    __table_args__ = (UniqueConstraint("org_id", name="uq_company_profiles_org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    revenue_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)  # CA annuel en €
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    certifications: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # Qualibat, ISO9001, MASE, etc.
    specialties: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # gros-oeuvre, electricite, plomberie, etc.
    regions: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # regions d'intervention
    max_market_size_eur: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # taille max marché capable de gérer
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="company_profile"
    )
