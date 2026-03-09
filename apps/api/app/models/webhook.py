"""Modèles pour les webhooks AO Copilot."""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WebhookEndpoint(Base):
    """URL cible d'un webhook configuré par l'utilisateur."""
    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))

    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)  # HMAC-SHA256 signing secret
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Événements souscrits (CSV)
    events: Mapped[str] = mapped_column(
        String(500),
        default="analysis.completed,project.created",
        server_default=text("'analysis.completed,project.created'"),
        nullable=False,
    )  # analysis.completed, project.created, project.deadline_due, quota.warning

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    failure_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan"
    )


class WebhookDelivery(Base):
    """Log de chaque tentative de livraison webhook."""
    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webhook_endpoints.id", ondelete="CASCADE"))

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    attempt_number: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    endpoint: Mapped["WebhookEndpoint"] = relationship("WebhookEndpoint", back_populates="deliveries")
