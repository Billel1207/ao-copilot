import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ChecklistAnnotation(Base):
    __tablename__ = "checklist_annotations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    checklist_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("checklist_items.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ao_projects.id", ondelete="CASCADE"), nullable=False
    )  # pour RLS
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )  # pour RLS
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    annotation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="comment"
    )  # "comment" | "question" | "validated" | "flag"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # Dénormalisé pour éviter les jointures coûteuses
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    checklist_item: Mapped["ChecklistItem"] = relationship("ChecklistItem")
    author: Mapped["User"] = relationship("User", foreign_keys=[user_id])
