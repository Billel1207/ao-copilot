"""Routes de facturation Stripe — checkout, portal, webhook, usage, subscription."""
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl
from typing import Literal

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org
from app.services.billing import billing_service, PLANS, UsageStats

router = APIRouter()
logger = structlog.get_logger(__name__)


# ── Schémas request/response ───────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: Literal["starter", "pro"]
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalRequest(BaseModel):
    return_url: str


class PortalResponse(BaseModel):
    portal_url: str


class UsageResponse(BaseModel):
    org_id: uuid.UUID
    plan: str
    plan_name: str
    docs_used_this_month: int
    docs_quota: int
    quota_pct: float
    period_year: int
    period_month: int
    word_export_allowed: bool
    plans_available: list[dict]


class SubscriptionResponse(BaseModel):
    org_id: uuid.UUID
    plan: str
    status: str
    stripe_subscription_id: str | None
    current_period_end: str | None
    cancel_at_period_end: bool


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée une session Stripe Checkout pour upgrader de plan."""
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut modifier l'abonnement")

    url = await billing_service.create_checkout_session(
        org=org,
        plan_id=body.plan,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        db=db,
        user_email=current_user.email,
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    body: PortalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée une session Customer Portal Stripe (gérer, annuler l'abonnement)."""
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    url = await billing_service.create_customer_portal_session(
        org=org,
        return_url=body.return_url,
        db=db,
    )
    return PortalResponse(portal_url=url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
):
    """Endpoint webhook Stripe — reçoit les événements (paiement, annulation...)."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Header stripe-signature manquant")

    payload = await request.body()

    result = await billing_service.handle_webhook(
        payload=payload,
        signature=stripe_signature,
        db=db,
    )
    return result


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne l'utilisation mensuelle de l'organisation et les infos de plan."""
    usage = await billing_service.get_usage(org.id, db)
    plan_config = PLANS.get(org.plan, PLANS["free"])

    plans_list = [
        {
            "id": pid,
            "name": p.name,
            "monthly_eur": p.monthly_eur,
            "docs_per_month": p.docs_per_month,
            "max_users": p.max_users,
            "word_export": p.word_export,
            "features": p.features,
        }
        for pid, p in PLANS.items()
        if pid != "business"  # Business est sur devis
    ]

    return UsageResponse(
        org_id=usage.org_id,
        plan=usage.plan,
        plan_name=plan_config.name,
        docs_used_this_month=usage.docs_used_this_month,
        docs_quota=usage.docs_quota,
        quota_pct=usage.quota_pct,
        period_year=usage.period_year,
        period_month=usage.period_month,
        word_export_allowed=usage.word_export_allowed,
        plans_available=plans_list,
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne l'abonnement Stripe actuel de l'organisation."""
    sub = await billing_service.get_subscription(org.id, db)

    if not sub:
        # Pas encore d'abonnement — retourner un état "free" virtuel
        return SubscriptionResponse(
            org_id=org.id,
            plan=org.plan,
            status="active",
            stripe_subscription_id=None,
            current_period_end=None,
            cancel_at_period_end=False,
        )

    return SubscriptionResponse(
        org_id=org.id,
        plan=sub.plan,
        status=sub.status,
        stripe_subscription_id=sub.stripe_subscription_id,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        cancel_at_period_end=sub.cancel_at_period_end,
    )
