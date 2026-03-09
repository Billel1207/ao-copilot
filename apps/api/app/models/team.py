"""Modèle TeamInvite — invitations à rejoindre une organisation."""
import uuid
import hashlib
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TeamInvite(Base):
    __tablename__ = "team_invites"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Token hashé SHA-256 (le token brut est envoyé par email, jamais stocké)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")  # member | admin
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization: Mapped["Organization"] = relationship("Organization")
    inviter: Mapped["User | None"] = relationship("User", foreign_keys=[invited_by])

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
