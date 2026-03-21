import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, String, ForeignKey, DateTime, Integer, JSON, text, UniqueConstraint
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

    # ── Champs étendus (Go/No-Go 9 dimensions) ───────────────────────────
    assurance_rc_montant: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Montant couverture RC Pro en €
    assurance_decennale: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )  # Assurance décennale souscrite ?
    partenaires_specialites: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # Spécialités couvertes par sous-traitants / partenaires
    marge_minimale_pct: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Marge brute minimale acceptée (%)
    max_projets_simultanes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Nombre max de projets en parallèle
    projets_actifs_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Nombre de projets actifs actuellement

    # ── White-labeling (plan Business) ─────────────────────────────
    logo_s3_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )  # Clé S3 du logo entreprise (PNG/SVG, max 2 Mo)
    custom_theme: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Surcharge couleurs exports: {"primary": "#...", "header_bg": "#..."}

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
