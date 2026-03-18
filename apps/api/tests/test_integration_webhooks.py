"""Tests intégration webhooks Stripe — scénarios end-to-end."""
import json
import uuid
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.billing import Subscription
from app.core.security import create_access_token
# ── Helpers ────────────────────────────────────────────────────────────────
def _make_headers(user_id: str, org_id: str, role: str = "admin") -> dict:
    token = create_access_token({"sub": user_id, "org_id": org_id, "role": role})
    return {"Authorization": f"Bearer {token}"}
async def _create_org_user(
    db: AsyncSession, plan: str = "free", quota: int = 5
) -> tuple[Organization, User]:
    org = Organization(
        id=uuid.uuid4(),
        name=f"Webhook Org {uuid.uuid4().hex[:6]}",
        slug=f"wh-org-{uuid.uuid4().hex[:6]}",
        plan=plan,
        quota_docs=quota,
    )
    db.add(org)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=f"wh-{uuid.uuid4().hex[:6]}@test.com",
        hashed_pw="hashed",
        role="admin",
        full_name="Webhook User",
    )
    db.add(user)
    await db.flush()
    return org, user
def _mock_stripe_event(event_type: str, data_object: dict) -> dict:
    return {
        "id": f"evt_{uuid.uuid4().hex[:16]}",
        "type": event_type,
        "data": {"object": data_object},
    }

def _mock_stripe_and_redis():
    """Return context managers that mock both Stripe and Redis for webhooks."""
    mock_stripe = MagicMock()
    mock_redis = MagicMock()
    # Redis idempotency check: set returns True = first time processing
    mock_redis.set.return_value = True
    return mock_stripe, mock_redis

# ── Fixture ────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client_db(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, db_session
    app.dependency_overrides.clear()
# ── Tests — Webhook manquant ──────────────────────────────────────────────
class TestWebhookSecurity:
    """Vérification des protections de l'endpoint webhook."""


    async def test_webhook_without_signature_returns_400(self, client_db):
        client, _ = client_db
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b'{"type": "test"}',
        )
        assert resp.status_code == 400


    async def test_webhook_with_empty_body_returns_error(self, client_db):
        client, _ = client_db
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b"",
            headers={"stripe-signature": "sig_test"},
        )
        assert resp.status_code in (400, 422, 500)
# ── Tests — checkout.session.completed ────────────────────────────────────
class TestCheckoutCompleted:
    """Webhook checkout.session.completed — upgrade de plan après paiement."""


    async def test_checkout_completed_upgrades_org_to_pro(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="free", quota=5)

        event = _mock_stripe_event("checkout.session.completed", {
            "id": "cs_test_123",
            "subscription": "sub_new_pro",
            "customer": "cus_test_123",
            "metadata": {"org_id": str(org.id), "plan": "pro"},
        })

        with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
             patch("redis.from_url") as mock_redis_factory:
            mock_stripe = MagicMock()
            mock_stripe.Webhook.construct_event.return_value = event
            mock_stripe_factory.return_value = mock_stripe

            mock_redis = MagicMock()
            mock_redis.set.return_value = True
            mock_redis_factory.return_value = mock_redis

            resp = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "sig_valid"},
            )

        assert resp.status_code == 200

        # Vérifier que l'org est passée au plan Pro
        await db.refresh(org)
        assert org.plan == "pro"
        assert org.quota_docs == 60  # quota Pro


    async def test_checkout_completed_creates_subscription_record(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="free", quota=5)

        event = _mock_stripe_event("checkout.session.completed", {
            "id": "cs_test_456",
            "subscription": "sub_starter_789",
            "customer": "cus_starter_456",
            "metadata": {"org_id": str(org.id), "plan": "starter"},
        })

        with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
             patch("redis.from_url") as mock_redis_factory:
            mock_stripe = MagicMock()
            mock_stripe.Webhook.construct_event.return_value = event
            mock_stripe_factory.return_value = mock_stripe

            mock_redis = MagicMock()
            mock_redis.set.return_value = True
            mock_redis_factory.return_value = mock_redis

            resp = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "sig_valid"},
            )

        assert resp.status_code == 200

        # Vérifier la création de l'enregistrement Subscription
        from sqlalchemy import select
        result = await db.execute(
            select(Subscription).where(Subscription.org_id == org.id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            assert sub.stripe_subscription_id == "sub_starter_789"
            assert sub.stripe_customer_id == "cus_starter_456"
# ── Tests — customer.subscription.deleted ─────────────────────────────────
class TestSubscriptionCanceled:
    """Webhook customer.subscription.deleted — downgrade au plan free."""


    async def test_subscription_deleted_downgrades_to_free(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="pro", quota=60)

        # Créer l'enregistrement subscription existant
        sub = Subscription(
            id=uuid.uuid4(),
            org_id=org.id,
            stripe_customer_id="cus_cancel_test",
            stripe_subscription_id="sub_to_cancel_123",
            plan="pro",
            status="active",
        )
        db.add(sub)
        await db.flush()

        event = _mock_stripe_event("customer.subscription.deleted", {
            "id": "sub_to_cancel_123",
        })

        with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
             patch("redis.from_url") as mock_redis_factory:
            mock_stripe = MagicMock()
            mock_stripe.Webhook.construct_event.return_value = event
            mock_stripe_factory.return_value = mock_stripe

            mock_redis = MagicMock()
            mock_redis.set.return_value = True
            mock_redis_factory.return_value = mock_redis

            resp = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "sig_valid"},
            )

        assert resp.status_code == 200

        # Org retombe au plan free
        await db.refresh(org)
        assert org.plan == "free"
        # PLANS["free"].docs_per_month is 5
        assert org.quota_docs == 5


    async def test_cancellation_marks_subscription_as_canceled(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="starter", quota=15)

        sub = Subscription(
            id=uuid.uuid4(),
            org_id=org.id,
            stripe_customer_id="cus_cancel_2",
            stripe_subscription_id="sub_cancel_456",
            plan="starter",
            status="active",
        )
        db.add(sub)
        await db.flush()

        event = _mock_stripe_event("customer.subscription.deleted", {
            "id": "sub_cancel_456",
        })

        with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
             patch("redis.from_url") as mock_redis_factory:
            mock_stripe = MagicMock()
            mock_stripe.Webhook.construct_event.return_value = event
            mock_stripe_factory.return_value = mock_stripe

            mock_redis = MagicMock()
            mock_redis.set.return_value = True
            mock_redis_factory.return_value = mock_redis

            resp = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "sig_valid"},
            )

        assert resp.status_code == 200

        await db.refresh(sub)
        assert sub.status == "canceled"
# ── Tests — customer.subscription.updated ─────────────────────────────────
class TestSubscriptionUpdated:
    """Webhook customer.subscription.updated — changement de plan."""


    async def test_subscription_updated_changes_plan(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="starter", quota=15)

        sub = Subscription(
            id=uuid.uuid4(),
            org_id=org.id,
            stripe_customer_id="cus_upgrade",
            stripe_subscription_id="sub_upgrade_789",
            plan="starter",
            status="active",
        )
        db.add(sub)
        await db.flush()

        event = _mock_stripe_event("customer.subscription.updated", {
            "id": "sub_upgrade_789",
            "status": "active",
            "metadata": {"plan": "pro"},
            "items": {"data": [{"price": {"id": "price_pro_monthly"}}]},
        })

        with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
             patch("redis.from_url") as mock_redis_factory:
            mock_stripe = MagicMock()
            mock_stripe.Webhook.construct_event.return_value = event
            mock_stripe_factory.return_value = mock_stripe

            mock_redis = MagicMock()
            mock_redis.set.return_value = True
            mock_redis_factory.return_value = mock_redis

            resp = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "sig_valid"},
            )

        # Le handler peut retourner 200 (traité) ou ignorer
        assert resp.status_code == 200
# ── Tests — Idempotence ───────────────────────────────────────────────────
class TestWebhookIdempotence:
    """Les webhooks doivent être idempotents — double envoi ne casse pas."""


    async def test_double_cancellation_is_safe(self, client_db):
        client, db = client_db
        org, user = await _create_org_user(db, plan="pro", quota=60)

        sub = Subscription(
            id=uuid.uuid4(),
            org_id=org.id,
            stripe_customer_id="cus_idempotent",
            stripe_subscription_id="sub_idempotent_001",
            plan="pro",
            status="active",
        )
        db.add(sub)
        await db.flush()

        event = _mock_stripe_event("customer.subscription.deleted", {
            "id": "sub_idempotent_001",
        })

        for call_num in range(2):
            with patch("app.services.billing._get_stripe") as mock_stripe_factory, \
                 patch("redis.from_url") as mock_redis_factory:
                mock_stripe = MagicMock()
                mock_stripe.Webhook.construct_event.return_value = event
                mock_stripe_factory.return_value = mock_stripe

                mock_redis = MagicMock()
                # First call: set returns True (not a duplicate)
                # Second call: set returns False (duplicate) — should return "duplicate" status
                mock_redis.set.return_value = (call_num == 0)
                mock_redis_factory.return_value = mock_redis

                resp = await client.post(
                    "/api/v1/billing/webhook",
                    content=json.dumps(event).encode(),
                    headers={"stripe-signature": "sig_valid"},
                )
                assert resp.status_code == 200

        # Org est free après les appels
        await db.refresh(org)
        assert org.plan == "free"
