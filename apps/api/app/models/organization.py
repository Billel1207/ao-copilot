import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    quota_docs: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    projects: Mapped[list["AoProject"]] = relationship("AoProject", back_populates="organization")
    company_profile: Mapped["CompanyProfile | None"] = relationship("CompanyProfile", back_populates="organization", uselist=False)
