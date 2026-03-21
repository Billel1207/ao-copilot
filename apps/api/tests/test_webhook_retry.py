"""Tests for Celery webhook tasks and billing service edge cases.

Covers:
- tasks._dispatch_export_webhook: project not found, no endpoints, delivery errors
- tasks._set_progress: Redis storage
- tasks._check_and_trigger_analysis: trigger logic
- BillingService: plan configs, enforce_quota bypass, webhook handler edge cases
"""
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# _dispatch_export_webhook
# ---------------------------------------------------------------------------

class TestDispatchExportWebhook:

    @patch("app.worker.tasks.SyncSession")
    def test_project_not_found_returns_silently(self, mock_session_cls):
        from app.worker.tasks import _dispatch_export_webhook

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_cls.return_value = mock_db

        # Should not raise
        _dispatch_export_webhook("nonexistent-id", "pdf", "exports/test.pdf")

    @patch("app.worker.tasks.SyncSession")
    def test_no_matching_endpoints(self, mock_session_cls):
        from app.worker.tasks import _dispatch_export_webhook

        mock_project = MagicMock()
        mock_project.org_id = uuid.uuid4()
        mock_project.title = "Test Project"

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
        # Endpoints query returns empty (no webhooks configured)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session_cls.return_value = mock_db

        # Should not raise
        _dispatch_export_webhook(str(uuid.uuid4()), "pdf", "exports/test.pdf")

    def test_outer_exception_caught_silently(self):
        """If the entire function fails (e.g., import error), it's caught."""
        from app.worker.tasks import _dispatch_export_webhook

        with patch("app.worker.tasks.SyncSession", side_effect=Exception("DB down")):
            # Should not raise
            _dispatch_export_webhook(str(uuid.uuid4()), "pdf", "exports/test.pdf")

    @patch("app.worker.tasks.SyncSession")
    def test_endpoint_subscribed_to_export_calls_deliver(self, mock_session_cls):
        """Endpoint with export.completed in events should trigger delivery."""
        from app.worker.tasks import _dispatch_export_webhook

        mock_project = MagicMock()
        mock_project.org_id = uuid.uuid4()
        mock_project.title = "Test"

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/hook"
        mock_ep.secret = "secret"
        mock_ep.events = "export.completed, analysis.completed"

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ep]
        mock_session_cls.return_value = mock_db

        with patch("app.services.webhook_dispatch.deliver_single_webhook_sync", return_value={"success": True}) as mock_deliver:
            _dispatch_export_webhook(str(uuid.uuid4()), "pdf", "exports/test.pdf")
            mock_deliver.assert_called_once()

    @patch("app.worker.tasks.SyncSession")
    def test_endpoint_not_subscribed_to_export_skips(self, mock_session_cls):
        """Endpoint without export.completed should NOT trigger delivery."""
        from app.worker.tasks import _dispatch_export_webhook

        mock_project = MagicMock()
        mock_project.org_id = uuid.uuid4()
        mock_project.title = "Test"

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/hook"
        mock_ep.secret = "secret"
        mock_ep.events = "analysis.completed"  # NOT export.completed

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ep]
        mock_session_cls.return_value = mock_db

        with patch("app.services.webhook_dispatch.deliver_single_webhook_sync") as mock_deliver:
            _dispatch_export_webhook(str(uuid.uuid4()), "pdf", "exports/test.pdf")
            mock_deliver.assert_not_called()

    @patch("app.worker.tasks.SyncSession")
    def test_delivery_exception_caught_per_endpoint(self, mock_session_cls):
        """Exception in deliver_single_webhook_sync should be caught per endpoint."""
        from app.worker.tasks import _dispatch_export_webhook

        mock_project = MagicMock()
        mock_project.org_id = uuid.uuid4()
        mock_project.title = "Test"

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/hook"
        mock_ep.secret = "secret"
        mock_ep.events = "export.completed"

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ep]
        mock_session_cls.return_value = mock_db

        with patch("app.services.webhook_dispatch.deliver_single_webhook_sync", side_effect=Exception("network")):
            # Should not raise
            _dispatch_export_webhook(str(uuid.uuid4()), "pdf", "exports/test.pdf")

    @patch("app.worker.tasks.SyncSession")
    def test_empty_events_string_skips(self, mock_session_cls):
        from app.worker.tasks import _dispatch_export_webhook

        mock_project = MagicMock()
        mock_project.org_id = uuid.uuid4()
        mock_project.title = "Test"

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/hook"
        mock_ep.secret = "secret"
        mock_ep.events = ""  # empty events

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ep]
        mock_session_cls.return_value = mock_db

        with patch("app.services.webhook_dispatch.deliver_single_webhook_sync") as mock_deliver:
            _dispatch_export_webhook(str(uuid.uuid4()), "memo", "exports/test.docx")
            mock_deliver.assert_not_called()


# ---------------------------------------------------------------------------
# _set_progress
# ---------------------------------------------------------------------------

class TestSetProgress:

    def test_stores_progress_in_redis(self):
        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            from app.worker.tasks import _set_progress
            _set_progress("task-123", 50, "Processing")
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "progress:task-123" in call_args[0]
        assert "50" in call_args[0][1]


# ---------------------------------------------------------------------------
# _check_and_trigger_analysis
# ---------------------------------------------------------------------------

class TestCheckAndTriggerAnalysis:

    def test_triggers_when_all_docs_done(self):
        from app.worker.tasks import _check_and_trigger_analysis

        mock_db = MagicMock()
        doc1 = MagicMock(status="done")
        doc2 = MagicMock(status="done")
        mock_db.query.return_value.filter_by.return_value.all.return_value = [doc1, doc2]

        with patch("app.worker.tasks.analyze_project") as mock_analyze:
            mock_analyze.delay = MagicMock()
            _check_and_trigger_analysis(mock_db, str(uuid.uuid4()))
            mock_analyze.delay.assert_called_once()

    def test_triggers_when_mixed_done_and_error(self):
        from app.worker.tasks import _check_and_trigger_analysis

        mock_db = MagicMock()
        doc1 = MagicMock(status="done")
        doc2 = MagicMock(status="error")
        mock_db.query.return_value.filter_by.return_value.all.return_value = [doc1, doc2]

        with patch("app.worker.tasks.analyze_project") as mock_analyze:
            mock_analyze.delay = MagicMock()
            _check_and_trigger_analysis(mock_db, str(uuid.uuid4()))
            mock_analyze.delay.assert_called_once()

    def test_does_not_trigger_when_all_error(self):
        from app.worker.tasks import _check_and_trigger_analysis

        mock_db = MagicMock()
        doc1 = MagicMock(status="error")
        doc2 = MagicMock(status="error")
        mock_db.query.return_value.filter_by.return_value.all.return_value = [doc1, doc2]

        with patch("app.worker.tasks.analyze_project") as mock_analyze:
            mock_analyze.delay = MagicMock()
            _check_and_trigger_analysis(mock_db, str(uuid.uuid4()))
            mock_analyze.delay.assert_not_called()

    def test_does_not_trigger_when_still_processing(self):
        from app.worker.tasks import _check_and_trigger_analysis

        mock_db = MagicMock()
        doc1 = MagicMock(status="done")
        doc2 = MagicMock(status="processing")
        mock_db.query.return_value.filter_by.return_value.all.return_value = [doc1, doc2]

        with patch("app.worker.tasks.analyze_project") as mock_analyze:
            mock_analyze.delay = MagicMock()
            _check_and_trigger_analysis(mock_db, str(uuid.uuid4()))
            mock_analyze.delay.assert_not_called()

    def test_does_not_trigger_when_no_docs(self):
        """Empty doc list: all() is vacuously true, but any() is false -> no trigger."""
        from app.worker.tasks import _check_and_trigger_analysis

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        with patch("app.worker.tasks.analyze_project") as mock_analyze:
            mock_analyze.delay = MagicMock()
            _check_and_trigger_analysis(mock_db, str(uuid.uuid4()))
            mock_analyze.delay.assert_not_called()


# ---------------------------------------------------------------------------
# BillingService — plan configuration edge cases
# ---------------------------------------------------------------------------

class TestBillingPlanConfig:

    def test_all_plans_defined(self):
        from app.services.billing import PLANS
        expected_plans = {"free", "trial", "starter", "pro", "europe", "business"}
        assert set(PLANS.keys()) == expected_plans

    def test_free_plan_has_zero_price(self):
        from app.services.billing import PLANS
        assert PLANS["free"].monthly_eur == 0.0

    def test_trial_plan_has_zero_price(self):
        from app.services.billing import PLANS
        assert PLANS["trial"].monthly_eur == 0.0

    def test_free_plan_no_word_export(self):
        from app.services.billing import PLANS
        assert PLANS["free"].word_export is False

    def test_paid_plans_have_word_export(self):
        from app.services.billing import PLANS
        for plan_id in ("starter", "pro", "europe", "business"):
            assert PLANS[plan_id].word_export is True, f"{plan_id} should have word_export"

    def test_business_plan_has_max_limits(self):
        from app.services.billing import PLANS
        biz = PLANS["business"]
        assert biz.docs_per_month == 999
        assert biz.max_users == 999
        assert biz.retention_days == 365

    def test_plan_retention_days_increase_with_price(self):
        from app.services.billing import PLANS
        assert PLANS["free"].retention_days < PLANS["starter"].retention_days
        assert PLANS["starter"].retention_days < PLANS["pro"].retention_days
        assert PLANS["pro"].retention_days < PLANS["europe"].retention_days
        assert PLANS["europe"].retention_days < PLANS["business"].retention_days

    def test_plan_docs_per_month_increase(self):
        from app.services.billing import PLANS
        assert PLANS["free"].docs_per_month < PLANS["starter"].docs_per_month
        assert PLANS["starter"].docs_per_month < PLANS["pro"].docs_per_month
        assert PLANS["pro"].docs_per_month < PLANS["europe"].docs_per_month

    def test_free_plan_no_stripe_price_id(self):
        from app.services.billing import PLANS
        assert PLANS["free"].stripe_price_id == ""

    def test_trial_plan_no_stripe_price_id(self):
        from app.services.billing import PLANS
        assert PLANS["trial"].stripe_price_id == ""

    def test_each_plan_has_features_list(self):
        from app.services.billing import PLANS
        for plan_id, plan in PLANS.items():
            assert isinstance(plan.features, list), f"{plan_id} features should be a list"
            assert len(plan.features) > 0, f"{plan_id} should have at least one feature"

    def test_plan_prices_are_correct(self):
        from app.services.billing import PLANS
        assert PLANS["starter"].monthly_eur == 69.0
        assert PLANS["pro"].monthly_eur == 179.0
        assert PLANS["europe"].monthly_eur == 299.0
        assert PLANS["business"].monthly_eur == 499.0


# ---------------------------------------------------------------------------
# BillingService.enforce_quota — bypass paths
# ---------------------------------------------------------------------------

class TestEnforceQuotaBypass:

    @pytest.mark.asyncio
    async def test_business_plan_bypasses_quota(self):
        from app.services.billing import billing_service

        org = MagicMock()
        org.plan = "business"
        org.quota_docs = 999
        db = AsyncMock()

        # Should not raise even if usage exceeds quota
        await billing_service.enforce_quota(org, db)

    @pytest.mark.asyncio
    async def test_high_quota_bypasses_enforcement(self):
        from app.services.billing import billing_service

        org = MagicMock()
        org.plan = "trial"
        org.quota_docs = 99999  # bypass threshold
        db = AsyncMock()

        await billing_service.enforce_quota(org, db)


# ---------------------------------------------------------------------------
# BillingService.create_checkout_session — edge cases
# ---------------------------------------------------------------------------

class TestCreateCheckoutSession:

    @pytest.mark.asyncio
    async def test_unknown_plan_raises_400(self):
        from app.services.billing import billing_service
        from fastapi import HTTPException

        org = MagicMock()
        org.id = uuid.uuid4()
        org.plan = "free"
        db = AsyncMock()

        with patch("app.services.billing.settings") as mock_settings:
            mock_settings.APP_ENV = "development"

            with pytest.raises(HTTPException) as exc_info:
                await billing_service.create_checkout_session(
                    org, "nonexistent_plan", "http://ok", "http://cancel", db
                )
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_dev_mode_bypasses_stripe(self):
        from app.services.billing import billing_service

        org = MagicMock()
        org.id = uuid.uuid4()
        org.plan = "free"
        db = AsyncMock()

        with patch("app.services.billing.settings") as mock_settings:
            mock_settings.APP_ENV = "development"

            url = await billing_service.create_checkout_session(
                org, "pro", "http://success", "http://cancel", db
            )
        assert url == "http://success"
        assert org.plan == "pro"


# ---------------------------------------------------------------------------
# BillingService webhook handler — edge cases
# ---------------------------------------------------------------------------

class TestBillingWebhookHandlers:

    @pytest.mark.asyncio
    async def test_checkout_missing_metadata_returns_early(self):
        from app.services.billing import billing_service

        db = AsyncMock()
        session_data = {"metadata": {}}  # missing org_id and plan

        await billing_service._handle_checkout_completed(session_data, db)
        # Should not have queried DB for org
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_checkout_org_not_found_returns_early(self):
        from app.services.billing import billing_service

        org_id = str(uuid.uuid4())
        session_data = {
            "metadata": {"org_id": org_id, "plan": "pro"},
            "subscription": "sub_123",
        }
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        await billing_service._handle_checkout_completed(session_data, db)

    @pytest.mark.asyncio
    async def test_subscription_updated_not_found(self):
        from app.services.billing import billing_service

        sub_data = {"id": "sub_nonexistent", "status": "active"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        # Should not raise
        await billing_service._handle_subscription_updated(sub_data, db)

    @pytest.mark.asyncio
    async def test_subscription_deleted_not_found(self):
        from app.services.billing import billing_service

        sub_data = {"id": "sub_nonexistent"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        await billing_service._handle_subscription_deleted(sub_data, db)

    @pytest.mark.asyncio
    async def test_invoice_paid_no_subscription_id(self):
        from app.services.billing import billing_service

        invoice_data = {"id": "inv_123"}  # no subscription key
        db = AsyncMock()

        await billing_service._handle_invoice_paid(invoice_data, db)
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_no_subscription(self):
        from app.services.billing import billing_service

        invoice_data = {"id": "inv_123"}  # no subscription key
        db = AsyncMock()

        await billing_service._handle_invoice_payment_failed(invoice_data, db)
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_sub_not_found(self):
        from app.services.billing import billing_service

        invoice_data = {"id": "inv_123", "subscription": "sub_xyz"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        # Should not raise
        await billing_service._handle_invoice_payment_failed(invoice_data, db)

    @pytest.mark.asyncio
    async def test_subscription_updated_with_period_dates(self):
        from app.services.billing import billing_service

        mock_sub = MagicMock()
        mock_sub.status = "active"

        sub_data = {
            "id": "sub_123",
            "status": "trialing",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "cancel_at_period_end": True,
        }
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub

        db = AsyncMock()
        db.execute.return_value = mock_result

        await billing_service._handle_subscription_updated(sub_data, db)

        assert mock_sub.status == "trialing"
        assert mock_sub.cancel_at_period_end is True
        assert mock_sub.current_period_start is not None
        assert mock_sub.current_period_end is not None

    @pytest.mark.asyncio
    async def test_subscription_updated_without_period_dates(self):
        from app.services.billing import billing_service

        mock_sub = MagicMock()
        mock_sub.status = "active"
        mock_sub.current_period_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_sub.current_period_end = datetime(2025, 2, 1, tzinfo=timezone.utc)
        original_start = mock_sub.current_period_start
        original_end = mock_sub.current_period_end

        sub_data = {
            "id": "sub_123",
            "status": "past_due",
            # No current_period_start/end
        }
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub

        db = AsyncMock()
        db.execute.return_value = mock_result

        await billing_service._handle_subscription_updated(sub_data, db)

        assert mock_sub.status == "past_due"
        # Period dates should remain unchanged
        assert mock_sub.current_period_start == original_start
        assert mock_sub.current_period_end == original_end

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_sets_past_due(self):
        from app.services.billing import billing_service

        mock_sub = MagicMock()
        mock_sub.status = "active"

        invoice_data = {"id": "inv_123", "subscription": "sub_xyz"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub

        db = AsyncMock()
        db.execute.return_value = mock_result

        await billing_service._handle_invoice_payment_failed(invoice_data, db)
        assert mock_sub.status == "past_due"

    @pytest.mark.asyncio
    async def test_checkout_with_unknown_plan_still_sets_org(self):
        """If plan_id is not in PLANS dict, org.plan and quota are not updated."""
        from app.services.billing import billing_service

        org_id = uuid.uuid4()
        session_data = {
            "metadata": {"org_id": str(org_id), "plan": "unknown_plan"},
            "subscription": "sub_abc",
        }

        mock_org = MagicMock()
        mock_org.plan = "free"
        mock_org.quota_docs = 2

        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = None

        mock_org_result = MagicMock()
        mock_org_result.scalar_one_or_none.return_value = mock_org
        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = mock_sub

        db = AsyncMock()
        db.execute.side_effect = [mock_org_result, mock_sub_result]

        await billing_service._handle_checkout_completed(session_data, db)
        # org.plan should remain "free" since "unknown_plan" not in PLANS
        assert mock_org.plan == "free"
        assert mock_org.quota_docs == 2


# ---------------------------------------------------------------------------
# UsageStats dataclass
# ---------------------------------------------------------------------------

class TestUsageStats:

    def test_usage_stats_creation(self):
        from app.services.billing import UsageStats

        org_id = uuid.uuid4()
        stats = UsageStats(
            org_id=org_id,
            plan="starter",
            docs_used_this_month=5,
            docs_quota=15,
            quota_pct=33.3,
            period_year=2026,
            period_month=3,
            word_export_allowed=True,
        )
        assert stats.plan == "starter"
        assert stats.docs_used_this_month == 5
        assert stats.quota_pct == 33.3
        assert stats.word_export_allowed is True

    def test_usage_stats_zero_usage(self):
        from app.services.billing import UsageStats

        stats = UsageStats(
            org_id=uuid.uuid4(),
            plan="free",
            docs_used_this_month=0,
            docs_quota=2,
            quota_pct=0.0,
            period_year=2026,
            period_month=1,
            word_export_allowed=False,
        )
        assert stats.docs_used_this_month == 0
        assert stats.quota_pct == 0.0
        assert stats.word_export_allowed is False
