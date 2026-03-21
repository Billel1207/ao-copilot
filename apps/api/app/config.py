import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

# Force-load .env BEFORE Pydantic reads os.environ
# (Claude Code sets ANTHROPIC_API_KEY="" in shell env which overrides .env)
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_ENV: Literal["development", "staging", "production"] = "development"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aocopilot:aocopilot_secret@localhost:5432/aocopilot"
    DATABASE_URL_SYNC: str = "postgresql://aocopilot:aocopilot_secret@localhost:5432/aocopilot"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "aocopilot_minio"
    S3_SECRET_KEY: str = "aocopilot_minio_secret"
    S3_BUCKET_NAME: str = "aocopilot-documents"
    S3_REGION: str = "fr-par"
    S3_SIGNED_URL_EXPIRY: int = 900

    # LLM (Anthropic Claude — moteur principal)
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 16384

    # Fallback LLM (OpenAI GPT-4o — activé si OPENAI_API_KEY est renseigné)
    LLM_FALLBACK_MODEL: str = "gpt-4o"

    # Embeddings — OpenAI (défaut) ou Mistral (EU/RGPD)
    OPENAI_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "openai"  # "openai" (défaut) ou "mistral" (EU RGPD)
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMS: int = 1536

    # Mistral (hébergé en France — RGPD natif)
    MISTRAL_API_KEY: str = ""
    MISTRAL_EMBEDDING_MODEL: str = "mistral-embed"

    # JWT — RS256 (asymmetric) en production, HS256 en dev/test
    JWT_ALGORITHM: str = "HS256"
    JWT_PRIVATE_KEY: str = ""   # PEM RSA private key (required for RS256)
    JWT_PUBLIC_KEY: str = ""    # PEM RSA public key (required for RS256)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PDF Renderer (feature flag)
    USE_WEASYPRINT: bool = False  # True pour activer WeasyPrint (CSS3 complet, nécessite deps système)

    # Sentry
    SENTRY_DSN: str = ""

    # Stripe Billing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = "price_1T9JtH01CSvduw4lzqagkbQQ"  # 69€/mois
    STRIPE_PRICE_PRO: str = "price_1T9Jv901CSvduw4lh0rVDHiQ"  # 179€/mois
    STRIPE_PRICE_EUROPE: str = "price_1T91vb01CSvduw4lFd3RvNL6"  # 299€/mois
    STRIPE_PRICE_BUSINESS: str = "price_1T9Fum01CSvduw4lo5gFEIbE"  # 499€/mois
    STRIPE_PRICE_DOC_UNIT: str = "price_1T9FwV01CSvduw4l4597ixbb"  # 3€/doc
    STRIPE_PUBLISHABLE_KEY: str = "" # pk_xxx pour le frontend

    # Email (Resend)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "AO Copilot <noreply@ao-copilot.fr>"
    FRONTEND_URL: str = "http://localhost:3000"

    # ─── e-Attestations.com ───────────────────────────────
    EATTESTATION_API_KEY: str = ""
    EATTESTATION_BASE_URL: str = "https://api.e-attestations.com/v2"

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

        if self.APP_ENV == "production":
            # In production, wildcard "*" is forbidden
            if "*" in origins:
                raise RuntimeError(
                    "CRITICAL: ALLOWED_ORIGINS contains '*' in production. "
                    "Specify explicit HTTPS origins (e.g. https://ao-copilot.fr)."
                )
            # Filter out non-HTTPS origins in production (warn instead of crash)
            safe_origins = [o for o in origins if o.startswith("https://")]
            if not safe_origins:
                # Fallback to ao-copilot.fr if no HTTPS origins configured
                safe_origins = ["https://ao-copilot.fr"]
            return safe_origins

        return origins


settings = Settings()

# ── Production safety guards ─────────────────────────────────────────────
if settings.APP_ENV == "production":
    if settings.SECRET_KEY == "change-me-in-production-min-32-chars":
        raise RuntimeError(
            "CRITICAL: SECRET_KEY has the default value. "
            "Set a strong random secret (min 32 chars) in .env before running in production."
        )
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "CRITICAL: ANTHROPIC_API_KEY is empty. AI analysis requires a valid API key."
        )
    if not settings.STRIPE_SECRET_KEY:
        import logging as _log
        _log.getLogger(__name__).warning(
            "STRIPE_SECRET_KEY is empty — billing features will be unavailable"
        )
