import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Float, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AoProject(Base):
    __tablename__ = "ao_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buyer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # travaux|services|fournitures
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|analyzing|ready|archived
    submission_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Win/Loss tracking (R4)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)  # won|lost|no_bid
    result_amount_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=lambda: datetime.now(timezone.utc))

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    documents: Mapped[list["AoDocument"]] = relationship("AoDocument", back_populates="project", cascade="all, delete-orphan")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship("ChecklistItem", back_populates="project", cascade="all, delete-orphan")
    criteria_items: Mapped[list["CriteriaItem"]] = relationship("CriteriaItem", back_populates="project", cascade="all, delete-orphan")
    extraction_results: Mapped[list["ExtractionResult"]] = relationship("ExtractionResult", back_populates="project", cascade="all, delete-orphan")
    deadlines: Mapped[list["ProjectDeadline"]] = relationship("ProjectDeadline", back_populates="project", cascade="all, delete-orphan")
