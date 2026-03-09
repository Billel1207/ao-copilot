"""Routes pour la gestion des clés API et webhooks (Developer Settings)."""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.webhook import WebhookEndpoint, WebhookDelivery

router = APIRouter()

# ─── Clés API ─────────────────────────────────────────────────────────────────


class ApiKeyCreate(BaseModel):
    name: str
    can_write_projects: bool = False
    can_trigger_analysis: bool = False
    rate_limit_per_minute: int = 60


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    can_read_projects: bool
    can_write_projects: bool
    can_read_analysis: bool
    can_trigger_analysis: bool
    rate_limit_per_minute: int
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedOut(ApiKeyOut):
    """Retourné UNE SEULE FOIS à la création, contient la clé en clair."""
    full_key: str


def _hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


@router.get("/keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.org_id == current_user.org_id,
            ApiKey.revoked_at == None,  # noqa: E711
        )
    )
    return result.scalars().all()


@router.post("/keys", response_model=ApiKeyCreatedOut, status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'admin peut créer des clés API")

    # Générer la clé en clair: aoc_[32 chars hexadécimaux]
    random_part = secrets.token_hex(16)  # 32 hex chars
    full_key = f"aoc_{random_part}"
    key_prefix = f"aoc_{random_part[:4]}"

    api_key = ApiKey(
        org_id=current_user.org_id,
        created_by=current_user.id,
        name=data.name,
        key_prefix=key_prefix,
        key_hash=_hash_api_key(full_key),
        can_write_projects=data.can_write_projects,
        can_trigger_analysis=data.can_trigger_analysis,
        rate_limit_per_minute=data.rate_limit_per_minute,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    # Retourner la clé en clair UNE SEULE FOIS
    result = ApiKeyCreatedOut(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        can_read_projects=api_key.can_read_projects,
        can_write_projects=api_key.can_write_projects,
        can_read_analysis=api_key.can_read_analysis,
        can_trigger_analysis=api_key.can_trigger_analysis,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        full_key=full_key,
    )
    return result


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'admin peut révoquer des clés API")

    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == current_user.org_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Clé API introuvable")

    key.revoked_at = datetime.now(timezone.utc)
    key.is_active = False
    await db.commit()
    return {"ok": True}


# ─── Webhooks ──────────────────────────────────────────────────────────────────


class WebhookCreate(BaseModel):
    url: str
    description: Optional[str] = None
    events: list[str] = ["analysis.completed", "project.created"]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("https://") and not v.startswith("http://"):
            raise ValueError("L'URL doit commencer par http:// ou https://")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        from app.services.webhook_service import WEBHOOK_EVENTS
        invalid = [e for e in v if e not in WEBHOOK_EVENTS]
        if invalid:
            raise ValueError(f"Événements invalides : {invalid}. Valides : {WEBHOOK_EVENTS}")
        return v


class WebhookOut(BaseModel):
    id: uuid.UUID
    url: str
    description: Optional[str]
    events: list[str]
    is_active: bool
    failure_count: int
    last_delivery_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryOut(BaseModel):
    id: uuid.UUID
    event_type: str
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    attempt_number: int
    delivered_at: datetime

    class Config:
        from_attributes = True


def _endpoint_to_out(ep: WebhookEndpoint) -> WebhookOut:
    return WebhookOut(
        id=ep.id,
        url=ep.url,
        description=ep.description,
        events=ep.events.split(",") if ep.events else [],
        is_active=ep.is_active,
        failure_count=ep.failure_count,
        last_delivery_at=ep.last_delivery_at,
        created_at=ep.created_at,
    )


@router.get("/webhooks", response_model=list[WebhookOut])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.org_id == current_user.org_id)
    )
    endpoints = result.scalars().all()
    return [_endpoint_to_out(ep) for ep in endpoints]


@router.post("/webhooks", response_model=WebhookOut, status_code=201)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'admin peut créer des webhooks")

    signing_secret = secrets.token_hex(32)

    endpoint = WebhookEndpoint(
        org_id=current_user.org_id,
        url=data.url,
        secret=signing_secret,
        description=data.description,
        events=",".join(data.events),
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)

    return _endpoint_to_out(endpoint)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == current_user.org_id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    await db.delete(endpoint)
    await db.commit()
    return {"ok": True}


@router.get("/webhooks/{webhook_id}/deliveries", response_model=list[WebhookDeliveryOut])
async def list_webhook_deliveries(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier ownership
    ep_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == current_user.org_id,
        )
    )
    if not ep_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    del_result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(50)
    )
    return del_result.scalars().all()


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envoie un événement de test au webhook."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == current_user.org_id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    from app.services.webhook_service import dispatch_webhook
    await dispatch_webhook(
        db=db,
        org_id=str(current_user.org_id),
        event_type="test.ping",
        payload={
            "message": "Test de connectivité AO Copilot",
            "endpoint_url": endpoint.url,
        },
    )
    return {"ok": True, "message": "Événement de test envoyé"}
