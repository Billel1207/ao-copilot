"""Tests pour le dispatch de webhooks (webhook_dispatch.py).

Couvre :
- deliver_single_webhook_sync : succès, échec HTTP, timeout
- get_subscribed_endpoints : filtre event_type, is_active, failure_count
- _is_safe_url : protection SSRF
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.services.webhook_dispatch import (
    _is_safe_url,
    deliver_single_webhook_sync,
    get_subscribed_endpoints,
    MAX_FAILURE_COUNT,
    WEBHOOK_TIMEOUT,
)


# ── _is_safe_url tests ──────────────────────────────────────────────────

@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_rejects_private_ipv4_127():
    """URL pointant vers 127.0.0.1 → rejetée (SSRF)."""
    with patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("127.0.0.1", 443)),
    ]):
        assert _is_safe_url("https://localhost/webhook") is False


@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_rejects_private_ipv4_10():
    """URL résolvant vers 10.x.x.x → rejetée (SSRF)."""
    with patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("10.0.0.1", 443)),
    ]):
        assert _is_safe_url("https://internal.example.com/hook") is False


@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_rejects_private_ipv4_192_168():
    """URL résolvant vers 192.168.x.x → rejetée (SSRF)."""
    with patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("192.168.1.1", 443)),
    ]):
        assert _is_safe_url("https://myrouter.local/hook") is False


@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_allows_public_ip():
    """URL résolvant vers IP publique → acceptée."""
    with patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("93.184.216.34", 443)),
    ]):
        assert _is_safe_url("https://example.com/webhook") is True


@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_rejects_http_in_production():
    """HTTP rejeté en production (schéma non sécurisé)."""
    assert _is_safe_url("http://example.com/webhook") is False


@patch.dict("os.environ", {"ENV": "development"})
def test_ssrf_allows_http_in_dev():
    """HTTP autorisé en développement."""
    with patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("93.184.216.34", 80)),
    ]):
        assert _is_safe_url("http://example.com/webhook") is True


@patch.dict("os.environ", {"ENV": "production"})
def test_ssrf_rejects_dns_failure():
    """DNS failure → rejeté."""
    import socket
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("DNS failed")):
        assert _is_safe_url("https://nonexistent.invalid/hook") is False


def test_ssrf_rejects_empty_url():
    """URL vide / sans hostname → rejetée."""
    assert _is_safe_url("") is False
    assert _is_safe_url("not-a-url") is False


# ── deliver_single_webhook_sync tests ────────────────────────────────────

def _setup_deliver_mocks():
    """Helper: return (mock_session, mock_ep, patchers) for deliver tests."""
    mock_ep = MagicMock()
    mock_ep.failure_count = 0
    mock_ep.last_delivery_at = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_ep

    mock_engine = MagicMock()

    return mock_session, mock_ep, mock_engine


@patch("sqlalchemy.orm.sessionmaker")
@patch("sqlalchemy.create_engine")
def test_deliver_success_http_200(mock_create_engine, mock_sessionmaker):
    """Livraison webhook réussie (HTTP 200) → success=True."""
    mock_session, mock_ep, mock_engine = _setup_deliver_mocks()
    mock_create_engine.return_value = mock_engine
    mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value = mock_client_instance

        result = deliver_single_webhook_sync(
            endpoint_id=str(uuid.uuid4()),
            url="https://example.com/webhook",
            secret="test-secret",
            event_type="analysis.completed",
            payload_json='{"event":"test"}',
            attempt_number=1,
        )

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["error"] is None
    assert mock_ep.failure_count == 0


@patch("sqlalchemy.orm.sessionmaker")
@patch("sqlalchemy.create_engine")
def test_deliver_failure_http_500(mock_create_engine, mock_sessionmaker):
    """HTTP 500 → success=False, failure_count incrémenté."""
    mock_session, mock_ep, mock_engine = _setup_deliver_mocks()
    mock_ep.failure_count = 3
    mock_create_engine.return_value = mock_engine
    mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value = mock_client_instance

        result = deliver_single_webhook_sync(
            endpoint_id=str(uuid.uuid4()),
            url="https://example.com/webhook",
            secret="test-secret",
            event_type="analysis.completed",
            payload_json='{"event":"test"}',
            attempt_number=1,
        )

    assert result["success"] is False
    assert result["status_code"] == 500
    assert "HTTP 500" in result["error"]
    assert mock_ep.failure_count == 4


@patch("sqlalchemy.orm.sessionmaker")
@patch("sqlalchemy.create_engine")
def test_deliver_timeout_exception(mock_create_engine, mock_sessionmaker):
    """Timeout → success=False, error_message contient l'exception."""
    mock_session, mock_ep, mock_engine = _setup_deliver_mocks()
    mock_create_engine.return_value = mock_engine
    mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

    import httpx as _httpx

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.side_effect = _httpx.TimeoutException("Connection timed out")
        MockClient.return_value = mock_client_instance

        result = deliver_single_webhook_sync(
            endpoint_id=str(uuid.uuid4()),
            url="https://slow.example.com/webhook",
            secret="test-secret",
            event_type="analysis.completed",
            payload_json='{"event":"test"}',
            attempt_number=1,
        )

    assert result["success"] is False
    assert result["status_code"] is None
    assert "timed out" in result["error"].lower() or "Timeout" in result["error"]
    assert mock_ep.failure_count == 1


@patch("sqlalchemy.orm.sessionmaker")
@patch("sqlalchemy.create_engine")
def test_deliver_resets_failure_count_on_success(mock_create_engine, mock_sessionmaker):
    """Après des échecs, un succès remet failure_count à 0."""
    mock_session, mock_ep, mock_engine = _setup_deliver_mocks()
    mock_ep.failure_count = 7
    mock_create_engine.return_value = mock_engine
    mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 201

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value = mock_client_instance

        result = deliver_single_webhook_sync(
            endpoint_id=str(uuid.uuid4()),
            url="https://example.com/webhook",
            secret="test-secret",
            event_type="project.created",
            payload_json='{"event":"test"}',
            attempt_number=2,
        )

    assert result["success"] is True
    assert mock_ep.failure_count == 0


# ── get_subscribed_endpoints tests ───────────────────────────────────────

def _make_webhook_endpoint(
    org_id: uuid.UUID,
    url: str = "https://example.com/hook",
    events: str = "analysis.completed,project.created",
    is_active: bool = True,
    failure_count: int = 0,
):
    ep = MagicMock()
    ep.id = uuid.uuid4()
    ep.org_id = org_id
    ep.url = url
    ep.secret = "whsec_test123"
    ep.events = events
    ep.is_active = is_active
    ep.failure_count = failure_count
    return ep


@pytest.mark.asyncio
async def test_get_subscribed_filters_by_event_type():
    """Seuls les endpoints abonnés à l'event_type sont retournés."""
    org_id = uuid.uuid4()
    ep1 = _make_webhook_endpoint(org_id, events="analysis.completed")
    ep2 = _make_webhook_endpoint(org_id, events="project.created")

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [ep1, ep2]
    db.execute.return_value = result_mock

    with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
        endpoints = await get_subscribed_endpoints(db, str(org_id), "analysis.completed")

    assert len(endpoints) == 1
    assert endpoints[0]["endpoint_id"] == str(ep1.id)


@pytest.mark.asyncio
async def test_get_subscribed_excludes_high_failure_count():
    """Endpoints avec failure_count >= MAX_FAILURE_COUNT sont exclus par la query DB."""
    org_id = uuid.uuid4()
    ep_ok = _make_webhook_endpoint(org_id, failure_count=5, events="analysis.completed")

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [ep_ok]
    db.execute.return_value = result_mock

    with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
        endpoints = await get_subscribed_endpoints(db, str(org_id), "analysis.completed")

    assert len(endpoints) == 1


@pytest.mark.asyncio
async def test_get_subscribed_skips_unsafe_urls():
    """Endpoints avec URL non-safe (SSRF) sont exclus."""
    org_id = uuid.uuid4()
    ep = _make_webhook_endpoint(org_id, url="http://10.0.0.1/internal", events="analysis.completed")

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [ep]
    db.execute.return_value = result_mock

    with patch("app.services.webhook_dispatch._is_safe_url", return_value=False):
        endpoints = await get_subscribed_endpoints(db, str(org_id), "analysis.completed")

    assert len(endpoints) == 0


@pytest.mark.asyncio
async def test_get_subscribed_returns_empty_when_no_match():
    """Aucun endpoint abonné → liste vide."""
    org_id = uuid.uuid4()

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute.return_value = result_mock

    endpoints = await get_subscribed_endpoints(db, str(org_id), "quota.warning")
    assert endpoints == []


def test_max_failure_count_constant():
    """MAX_FAILURE_COUNT est 10."""
    assert MAX_FAILURE_COUNT == 10
