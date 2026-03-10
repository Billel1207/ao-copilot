"""Service de facturation Stripe — gestion abonnements, webhooks, quotas."""
import uuid
import structlog
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from fastapi import HTTPException

from app.config import settings
from app.models.billing import Subscription, Invoice, UsageRecord
from app.models.organization import Organization
from app.models.document import AoDocument
from app.models.project import AoProject

logger = structlog.get_logger(__name__)

# ── Lazy Stripe init ───────────────────────────────────────────────────────
_stripe = None


def _get_stripe():
    global _stripe
    if _stripe is None:
        try:
            import stripe as _stripe_lib
            _stripe_lib.api_key = settings.STRIPE_SECRET_KEY
            _stripe = _stripe_lib
        except ImportError:
            logger.error("stripe_not_installed", hint="pip install stripe>=9.0.0")
            raise RuntimeError("Stripe SDK non installé. Ajoutez stripe>=9.0.0 dans requirements.txt")
    return _stripe


# ── Plans configuration ────────────────────────────────────────────────────

PlanId = Literal["free", "trial", "starter", "pro", "europe", "business"]


@dataclass
class PlanConfig:
    name: str
    docs_per_month: int
    max_users: int
    monthly_eur: float
    stripe_price_id: str
    retention_days: int
    word_export: bool
    features: list[str]


PLANS: dict[PlanId, PlanConfig] = {
    "free": PlanConfig(
        name="Gratuit",
        docs_per_month=5,
        max_users=1,
        monthly_eur=0.0,
        stripe_price_id="",
        retention_days=14,
        word_export=False,
        features=["5 documents/mois", "1 utilisateur", "Analyse IA basique", "14 jours de rétention"],
    ),
    "trial": PlanConfig(
        name="Essai 14 jours",
        docs_per_month=15,
        max_users=1,
        monthly_eur=0.0,
        stripe_price_id="",
        retention_days=30,
        word_export=True,
        features=["15 documents/mois", "1 utilisateur", "Analyse IA complète", "Export Word", "14 jours gratuits"],
    ),
    "starter": PlanConfig(
        name="Starter",
        docs_per_month=15,
        max_users=1,
        monthly_eur=69.0,
        stripe_price_id=settings.STRIPE_PRICE_STARTER,
        retention_days=30,
        word_export=True,
        features=["15 documents/mois", "1 utilisateur", "Analyse IA complète", "Export PDF + Word", "Support email"],
    ),
    "pro": PlanConfig(
        name="Pro",
        docs_per_month=60,
        max_users=5,
        monthly_eur=179.0,
        stripe_price_id=settings.STRIPE_PRICE_PRO,
        retention_days=90,
        word_export=True,
        features=[
            "60 documents/mois",
            "5 utilisateurs",
            "Analyse IA complète",
            "Export PDF + Word + Excel",
            "Gestion équipe",
            "Support prioritaire",
        ],
    ),
    "europe": PlanConfig(
        name="Europe",
        docs_per_month=100,
        max_users=20,
        monthly_eur=299.0,
        stripe_price_id=settings.STRIPE_PRICE_EUROPE,
        retention_days=180,
        word_export=True,
        features=[
            "100 documents/mois",
            "20 utilisateurs",
            "Export Word inclus",
            "Monitoring TED (UE)",
            "Wallonie & Luxembourg",
            "Analyse IA complète",
            "Support prioritaire",
        ],
    ),
    "business": PlanConfig(
        name="Business",
        docs_per_month=999,
        max_users=999,
        monthly_eur=499.0,
        stripe_price_id=settings.STRIPE_PRICE_BUSINESS,
        retention_days=365,
        word_export=True,
        features=[
            "Documents illimités",
            "Utilisateurs illimités",
            "SSO SAML",
            "SLA 99.9%",
            "Onboarding dédié",
            "API webhooks",
            "Export PDF + Word + Excel",
            "Support dédié",
        ],
    ),
}


@dataclass
class UsageStats:
    org_id: uuid.UUID
    plan: str
    docs_used_this_month: int
    docs_quota: int
    quota_pct: float
    period_year: int
    period_month: int
    word_export_allowed: bool


class BillingService:
    """Service centralisé pour la facturation Stripe."""

    async def get_or_create_customer(
        self,
        org: Organization,
        db: AsyncSession,
        user_email: str | None = None,
    ) -> Subscription:
        """Récupère ou crée un customer Stripe + subscription record.

        ⚠️ Commit immédiat après création pour éviter les customers Stripe orphelins :
        Si stripe.checkout.Session.create() échoue APRÈS la création du customer,
        la transaction HTTP se rollback → perte du stripe_customer_id en DB,
        mais le customer Stripe reste dans Stripe → orphelin cumulatif.
        Fix : commit séparé du stripe_customer_id AVANT la tentative de checkout.
        """
        result = await db.execute(
            select(Subscription).where(Subscription.org_id == org.id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            return sub

        # Créer le customer Stripe
        stripe = _get_stripe()
        customer = stripe.Customer.create(
            email=user_email,
            name=org.name,
            metadata={"org_id": str(org.id), "plan": org.plan},
        )
        logger.info(
            "stripe_customer_created",
            customer_id=customer["id"],
            org_id=str(org.id),
        )

        sub = Subscription(
            org_id=org.id,
            stripe_customer_id=customer["id"],
            plan=org.plan,
            status="active",
        )
        db.add(sub)
        # Commit immédiat : persiste le stripe_customer_id indépendamment de la suite.
        # Si le checkout échoue après, le customer est retrouvé lors du retry (pas d'orphelin).
        await db.commit()
        await db.refresh(sub)
        return sub

    async def create_checkout_session(
        self,
        org: Organization,
        plan_id: PlanId,
        success_url: str,
        cancel_url: str,
        db: AsyncSession,
        user_email: str | None = None,
    ) -> str:
        """Crée une session Stripe Checkout et retourne l'URL de redirection."""
        # Guard : clé Stripe manquante → 503 clair au lieu d'une AuthenticationError Stripe
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=503,
                detail="Service de paiement non configuré. Contactez le support.",
            )

        if plan_id not in PLANS:
            raise HTTPException(status_code=400, detail=f"Plan inconnu : {plan_id}")

        plan = PLANS[plan_id]
        if not plan.stripe_price_id:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Service de paiement non configuré pour le plan '{plan_id}'. "
                    "Contactez le support."
                ),
            )

        stripe = _get_stripe()
        sub = await self.get_or_create_customer(org, db, user_email=user_email)

        try:
            session = stripe.checkout.Session.create(
                customer=sub.stripe_customer_id,
                # Moyens de paiement pour abonnements (mode subscription) :
                # CB + Apple Pay + Google Pay (via "card")
                # SEPA Debit désactivé par défaut — nécessite activation dans Stripe Dashboard
                payment_method_types=["card"],
                line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata={"org_id": str(org.id), "plan": plan_id},
                locale="fr",
                # Options UX B2B
                allow_promotion_codes=True,
                billing_address_collection="required",
                # tax_id_collection nécessite customer_update pour mettre à jour nom/adresse
                tax_id_collection={"enabled": True},
                customer_update={"address": "auto", "name": "auto"},
            )
        except stripe.error.InvalidRequestError as e:
            logger.error("stripe_checkout_invalid_request", error=str(e))
            raise HTTPException(
                status_code=400,
                detail=f"Erreur Stripe : {e.user_message or str(e)}",
            )
        except stripe.error.StripeError as e:
            logger.error("stripe_checkout_error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail="Service de paiement temporairement indisponible. Veuillez réessayer.",
            )
        return session["url"]

    async def create_customer_portal_session(
        self,
        org: Organization,
        return_url: str,
        db: AsyncSession,
    ) -> str:
        """Crée une session Customer Portal Stripe (gestion abonnement)."""
        stripe = _get_stripe()
        sub = await self.get_or_create_customer(org, db)

        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=return_url,
        )
        return session["url"]

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
        db: AsyncSession,
    ) -> dict:
        """Traite les événements webhook Stripe et met à jour la BD."""
        stripe = _get_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning("stripe_webhook_invalid_signature", error=str(e))
            raise HTTPException(status_code=400, detail="Signature webhook invalide")

        event_type = event["type"]
        event_id = event.get("id", "")
        data = event["data"]["object"]

        logger.info("stripe_webhook_received", event_type=event_type, event_id=event_id)

        # Idempotency — skip already-processed events (Redis SET NX with 48h TTL)
        if event_id:
            try:
                import redis as redis_lib
                r = redis_lib.from_url(settings.CELERY_BROKER_URL, socket_timeout=2)
                cache_key = f"stripe_event:{event_id}"
                if not r.set(cache_key, "1", nx=True, ex=172800):  # 48h TTL
                    logger.info("stripe_webhook_duplicate_skipped", event_id=event_id)
                    return {"status": "duplicate", "event": event_type}
            except Exception:
                pass  # Redis down — process anyway (at-least-once is better than skipping)

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(data, db)

        elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
            await self._handle_subscription_updated(data, db)

        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data, db)

        elif event_type == "invoice.paid":
            await self._handle_invoice_paid(data, db)

        elif event_type == "invoice.payment_failed":
            await self._handle_invoice_payment_failed(data, db)

        return {"status": "processed", "event": event_type}

    async def _handle_checkout_completed(self, session_data: dict, db: AsyncSession) -> None:
        """Checkout terminé → activer l'abonnement."""
        org_id_str = session_data.get("metadata", {}).get("org_id")
        plan_id = session_data.get("metadata", {}).get("plan")
        subscription_id = session_data.get("subscription")

        if not org_id_str or not plan_id:
            logger.warning("stripe_checkout_missing_metadata", data=session_data)
            return

        org_id = uuid.UUID(org_id_str)

        # Mettre à jour l'org
        org_result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = org_result.scalar_one_or_none()
        if not org:
            logger.error("stripe_checkout_org_not_found", org_id=org_id_str)
            return

        plan_config = PLANS.get(plan_id)
        if plan_config:
            org.plan = plan_id
            org.quota_docs = plan_config.docs_per_month

        # Mettre à jour la subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.org_id == org_id))
        sub = sub_result.scalar_one_or_none()
        if sub and subscription_id:
            sub.stripe_subscription_id = subscription_id
            sub.plan = plan_id
            sub.status = "active"

        await db.flush()
        logger.info("stripe_checkout_activated", org_id=org_id_str, plan=plan_id)

    async def _handle_subscription_updated(self, sub_data: dict, db: AsyncSession) -> None:
        """Abonnement mis à jour (upgrade/downgrade)."""
        stripe_sub_id = sub_data.get("id")
        status = sub_data.get("status", "active")

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return

        sub.status = status
        if sub_data.get("current_period_start"):
            sub.current_period_start = datetime.fromtimestamp(
                sub_data["current_period_start"], tz=timezone.utc
            )
        if sub_data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(
                sub_data["current_period_end"], tz=timezone.utc
            )
        sub.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
        await db.flush()

    async def _handle_subscription_deleted(self, sub_data: dict, db: AsyncSession) -> None:
        """Abonnement annulé → revenir au plan gratuit."""
        stripe_sub_id = sub_data.get("id")
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return

        sub.status = "canceled"
        sub.plan = "free"

        # Rétrograder l'org
        org_result = await db.execute(select(Organization).where(Organization.id == sub.org_id))
        org = org_result.scalar_one_or_none()
        if org:
            org.plan = "free"
            org.quota_docs = PLANS["free"].docs_per_month

        await db.flush()
        logger.info("stripe_subscription_canceled", org_id=str(sub.org_id))

    async def _handle_invoice_paid(self, invoice_data: dict, db: AsyncSession) -> None:
        """Facture payée → créer un enregistrement Invoice."""
        stripe_inv_id = invoice_data.get("id")
        stripe_sub_id = invoice_data.get("subscription")

        if not stripe_sub_id:
            return

        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return

        # Éviter les doublons
        existing = await db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_inv_id)
        )
        if existing.scalar_one_or_none():
            return

        amount_eur = (invoice_data.get("amount_paid", 0) or 0) / 100.0
        inv = Invoice(
            subscription_id=sub.id,
            org_id=sub.org_id,
            stripe_invoice_id=stripe_inv_id,
            amount_eur=amount_eur,
            status="paid",
            invoice_pdf_url=invoice_data.get("invoice_pdf"),
            paid_at=datetime.now(timezone.utc),
        )
        db.add(inv)
        await db.flush()

    async def _handle_invoice_payment_failed(self, invoice_data: dict, db: AsyncSession) -> None:
        """Paiement échoué → mettre à jour le statut subscription."""
        stripe_sub_id = invoice_data.get("subscription")
        if not stripe_sub_id:
            return

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "past_due"
            await db.flush()

    async def get_usage(self, org_id: uuid.UUID, db: AsyncSession) -> UsageStats:
        """Retourne l'utilisation actuelle de l'organisation."""
        now = datetime.now(timezone.utc)

        # Récupérer l'org
        org_result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = org_result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organisation introuvable")

        # Compter les docs uploadés ce mois
        count_result = await db.execute(
            select(func.count(AoDocument.id))
            .join(AoProject, AoDocument.project_id == AoProject.id)
            .where(
                AoProject.org_id == org_id,
                extract("year", AoDocument.uploaded_at) == now.year,
                extract("month", AoDocument.uploaded_at) == now.month,
            )
        )
        docs_used = count_result.scalar_one() or 0

        plan_config = PLANS.get(org.plan, PLANS["free"])
        quota_pct = round(docs_used / org.quota_docs * 100, 1) if org.quota_docs > 0 else 0.0

        return UsageStats(
            org_id=org_id,
            plan=org.plan,
            docs_used_this_month=docs_used,
            docs_quota=org.quota_docs,
            quota_pct=quota_pct,
            period_year=now.year,
            period_month=now.month,
            word_export_allowed=plan_config.word_export,
        )

    async def enforce_quota(self, org: Organization, db: AsyncSession) -> None:
        """Lève HTTP 429 si le quota mensuel est atteint."""
        usage = await self.get_usage(org.id, db)
        if usage.docs_used_this_month >= org.quota_docs:
            raise HTTPException(
                status_code=429,
                detail=f"Quota mensuel atteint ({org.quota_docs} documents). "
                       f"Passez au plan supérieur sur /billing.",
            )

    async def get_subscription(self, org_id: uuid.UUID, db: AsyncSession) -> Subscription | None:
        """Retourne l'abonnement actif d'une organisation."""
        result = await db.execute(
            select(Subscription).where(Subscription.org_id == org_id)
        )
        return result.scalar_one_or_none()


# Singleton
billing_service = BillingService()
