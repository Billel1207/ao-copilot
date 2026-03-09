import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProjectDeadline(Base):
    __tablename__ = "project_deadlines"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False
    )
    deadline_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "remise_offres" | "visite_site" | "questions_acheteur" | "publication_resultats" | "autre"
    label: Mapped[str] = mapped_column(String(500), nullable=False)  # label humain extrait du texte
    deadline_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    project: Mapped["AoProject"] = relationship("AoProject", back_populates="deadlines")
