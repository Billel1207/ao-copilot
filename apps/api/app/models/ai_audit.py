"""Modèle AIAuditLog — traçabilité des appels LLM (AI Act Article 50).

Chaque appel au service LLM (Anthropic Claude ou OpenAI fallback) est journalisé
avec le modèle utilisé, les tokens consommés, la latence, et un hash du prompt
(pas le contenu brut, pour la confidentialité des documents clients).
"""
import uuid
import hashlib
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    # Contexte organisationnel (RLS compatible)
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ao_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── LLM call metadata ──
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. "anthropic", "openai"
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "claude-sonnet-4-20250514", "gpt-4o"

    # Type d'analyse effectuée
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "summary", "checklist", "ccap_analysis", "go_nogo", "memo_section"

    # Tokens et performance
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cached_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Hash SHA-256 du prompt (pas le contenu brut — confidentialité)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Résultat
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Métadonnées additionnelles (température, fallback utilisé, etc.)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), index=True
    )

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Hash un prompt pour traçabilité sans exposer le contenu."""
        return hashlib.sha256(prompt.encode()).hexdigest()
