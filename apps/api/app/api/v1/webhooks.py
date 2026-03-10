"""Routes API pour la gestion des webhooks (plan Business uniquement).

CRUD : créer, lister, supprimer des endpoints webhook + consulter les deliveries.
"""
import uuid
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_EVENTS = {
    "analysis.completed",
    "project.created",
    "project.deadline_due",
    "quota.warning",
}


# ── Schemas ───────────────────────────────────────────────────────────────

class WebhookCreateIn(BaseModel):
    url: str = Field(..., min_length=10, max_length=500)
    description: str | None = Field(None, max_length=200)
    events: list[str] = Field(
        default=["analysis.completed", "project.created"],
        description="Événements à écouter",
    )


class WebhookOut(BaseModel):
    id: str
    url: str
    description: str | None
    events: list[str]
    secret: str  # Affiché pour que l'utilisateur puisse vérifier les signatures
    is_active: bool
    failure_count: int
    last_delivery_at: str | None
    created_at: str


class WebhookDeliveryOut(BaseModel):
    id: str
    event_type: str
    status_code: int | None
    success: bool
    error_message: str | None
    delivered_at: str


# ── Helpers ───────────────────────────────────────────────────────────────

def _check_business_plan(org: Organization):
    if org.plan != "business":
        raise HTTPException(
            status_code=403,
            detail="Les webhooks sont disponibles uniquement sur le plan Business (499€/mois).",
        )


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WebhookOut])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Liste tous les endpoints webhook de l'organisation."""
    _check_business_plan(org)

    result = await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.org_id == org.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    endpoints = result.scalars().all()

    return [
        WebhookOut(
            id=str(ep.id),
            url=ep.url,
            description=ep.description,
            events=[e.strip() for e in ep.events.split(",")],
            secret=ep.secret,
            is_active=ep.is_active,
            failure_count=ep.failure_count,
            last_delivery_at=ep.last_delivery_at.isoformat() if ep.last_delivery_at else None,
            created_at=ep.created_at.isoformat(),
        )
        for ep in endpoints
    ]


@router.post("", response_model=WebhookOut, status_code=201)
async def create_webhook(
    body: WebhookCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée un nouvel endpoint webhook."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut créer des webhooks")

    # Valider les événements
    invalid = [e for e in body.events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Événements invalides : {invalid}. Valides : {sorted(VALID_EVENTS)}",
        )

    # Limite : max 5 webhooks par org
    count_result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.org_id == org.id)
    )
    if len(count_result.scalars().all()) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 webhooks par organisation")

    # Générer un secret de signature
    webhook_secret = f"whsec_{secrets.token_urlsafe(32)}"

    endpoint = WebhookEndpoint(
        org_id=org.id,
        url=body.url,
        description=body.description,
        events=",".join(body.events),
        secret=webhook_secret,
    )
    db.add(endpoint)
    await db.flush()
    await db.refresh(endpoint)

    logger.info("webhook_created", url=body.url, org_id=str(org.id))

    return WebhookOut(
        id=str(endpoint.id),
        url=endpoint.url,
        description=endpoint.description,
        events=[e.strip() for e in endpoint.events.split(",")],
        secret=endpoint.secret,
        is_active=endpoint.is_active,
        failure_count=endpoint.failure_count,
        last_delivery_at=None,
        created_at=endpoint.created_at.isoformat(),
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Supprime un endpoint webhook et tous ses logs de livraison."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut supprimer des webhooks")

    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == org.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    await db.delete(endpoint)
    await db.flush()

    logger.info("webhook_deleted", webhook_id=str(webhook_id), org_id=str(org.id))

    return {"status": "deleted", "webhook_id": str(webhook_id)}


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryOut])
async def list_deliveries(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Liste les 50 dernières livraisons d'un webhook."""
    _check_business_plan(org)

    # Vérifier que le webhook appartient à l'org
    ep_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == org.id,
        )
    )
    if not ep_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(50)
    )
    deliveries = result.scalars().all()

    return [
        WebhookDeliveryOut(
            id=str(d.id),
            event_type=d.event_type,
            status_code=d.status_code,
            success=d.success,
            error_message=d.error_message,
            delivered_at=d.delivered_at.isoformat(),
        )
        for d in deliveries
    ]
