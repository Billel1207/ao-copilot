"""Modèle AuditLog — journalisation RGPD des actions sensibles."""
import uuid
import hashlib
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    # L'utilisateur peut être null si non authentifié (tentative de connexion échouée)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Exemples : "project", "document", "auth", "billing", "team"
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # IP hashée SHA-256 pour conformité RGPD (pas de stockage d'IP brute)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Métadonnées additionnelles (ex: plan, doc_name, error...)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), index=True
    )

    @staticmethod
    def hash_ip(ip: str | None) -> str | None:
        """Hash une IP brute pour conformité RGPD."""
        if not ip:
            return None
        return hashlib.sha256(ip.encode()).hexdigest()
