"""Tests for app.services.webhook_dispatch — webhook dispatching and SSRF protection."""
import json
import hmac
import hashlib
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# _sign_payload
# ---------------------------------------------------------------------------

class TestSignPayload:
    def test_sign_payload_returns_hex_digest(self):
        from app.services.webhook_dispatch import _sign_payload
        payload = '{"event": "test"}'
        secret = "whsec_test123"
        signature = _sign_payload(payload, secret)
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert signature == expected

    def test_sign_payload_deterministic(self):
        from app.services.webhook_dispatch import _sign_payload
        sig1 = _sign_payload("data", "secret")
        sig2 = _sign_payload("data", "secret")
        assert sig1 == sig2

    def test_sign_payload_different_data(self):
        from app.services.webhook_dispatch import _sign_payload
        sig1 = _sign_payload("data1", "secret")
        sig2 = _sign_payload("data2", "secret")
        assert sig1 != sig2

    def test_sign_payload_different_secret(self):
        from app.services.webhook_dispatch import _sign_payload
        sig1 = _sign_payload("data", "secret_a")
        sig2 = _sign_payload("data", "secret_b")
        assert sig1 != sig2

    def test_sign_payload_empty_payload(self):
        from app.services.webhook_dispatch import _sign_payload
        sig = _sign_payload("", "secret")
        assert isinstance(sig, str) and len(sig) == 64

    def test_sign_payload_empty_secret(self):
        from app.services.webhook_dispatch import _sign_payload
        sig = _sign_payload("data", "")
        assert isinstance(sig, str) and len(sig) == 64

    def test_sign_payload_unicode(self):
        from app.services.webhook_dispatch import _sign_payload
        sig = _sign_payload('{"msg":"evenement termine"}', "cle_secrete")
        assert isinstance(sig, str) and len(sig) == 64


# ---------------------------------------------------------------------------
# _is_safe_url — SSRF protection
# ---------------------------------------------------------------------------

class TestIsSafeUrl:
    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_rejects_http_in_production(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        assert _is_safe_url("http://example.com/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_allows_https_in_production(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        assert _is_safe_url("https://example.com/webhook") is True

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "development"})
    def test_allows_http_in_development(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 80)),
        ]
        assert _is_safe_url("http://example.com/webhook") is True

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_localhost(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]
        assert _is_safe_url("https://localhost/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_private_ip_10(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("10.0.0.5", 443)),
        ]
        assert _is_safe_url("https://internal.corp/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_private_ip_192(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("192.168.1.100", 443)),
        ]
        assert _is_safe_url("https://router.local/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_private_ip_172(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("172.16.0.1", 443)),
        ]
        assert _is_safe_url("https://docker-host/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_link_local_169_254(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("169.254.1.1", 443)),
        ]
        assert _is_safe_url("https://link-local.example/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_blocks_ipv6_loopback(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (10, 1, 6, "", ("::1", 443, 0, 0)),
        ]
        assert _is_safe_url("https://ipv6-localhost/webhook") is False

    def test_rejects_empty_url(self):
        from app.services.webhook_dispatch import _is_safe_url
        assert _is_safe_url("") is False

    @patch.dict("os.environ", {"ENV": "production"})
    def test_rejects_no_hostname(self):
        from app.services.webhook_dispatch import _is_safe_url
        assert _is_safe_url("https://") is False

    @patch.dict("os.environ", {"ENV": "production"})
    def test_rejects_ftp_scheme(self):
        from app.services.webhook_dispatch import _is_safe_url
        assert _is_safe_url("ftp://example.com/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_dns_failure_returns_false(self, mock_socket):
        import socket as real_socket
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.side_effect = real_socket.gaierror("DNS failed")
        mock_socket.gaierror = real_socket.gaierror
        mock_socket.IPPROTO_TCP = real_socket.IPPROTO_TCP
        assert _is_safe_url("https://nonexistent.invalid/webhook") is False

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "local"})
    def test_local_env_allows_http(self, mock_socket):
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 80)),
        ]
        assert _is_safe_url("http://example.com/webhook") is True

    @patch("app.services.webhook_dispatch.socket")
    @patch.dict("os.environ", {"ENV": "production"})
    def test_multiple_ips_one_private_blocks_all(self, mock_socket):
        """If any resolved IP is private, the URL should be blocked."""
        from app.services.webhook_dispatch import _is_safe_url
        mock_socket.getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("10.0.0.1", 443)),  # private!
        ]
        assert _is_safe_url("https://example.com/webhook") is False


# ---------------------------------------------------------------------------
# deliver_single_webhook_sync
# ---------------------------------------------------------------------------

class TestDeliverSingleWebhookSync:
    """Tests for deliver_single_webhook_sync — patches httpx + sqlalchemy imports."""

    def _make_mock_session(self, failure_count=0):
        mock_session = MagicMock()
        mock_ep = MagicMock()
        mock_ep.failure_count = failure_count
        mock_session.get.return_value = mock_ep
        mock_session_factory = MagicMock(return_value=mock_session)
        return mock_session, mock_ep, mock_session_factory

    def _make_httpx_mock(self, status_code=200, side_effect=None):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        if side_effect:
            mock_client.post.side_effect = side_effect
        else:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_client.post.return_value = mock_response
        return mock_client

    def _run_delivery(self, mock_client, mock_session_factory, **kwargs):
        from app.services.webhook_dispatch import deliver_single_webhook_sync
        defaults = {
            "endpoint_id": str(uuid.uuid4()),
            "url": "https://example.com/webhook",
            "secret": "whsec_test",
            "event_type": "analysis.completed",
            "payload_json": '{"event": "analysis.completed"}',
            "attempt_number": 1,
        }
        defaults.update(kwargs)

        # create_engine and sessionmaker are imported INSIDE the function,
        # so we patch them at sqlalchemy level
        with patch("sqlalchemy.create_engine", return_value=MagicMock()), \
             patch("sqlalchemy.orm.sessionmaker", return_value=mock_session_factory):
            # httpx is also imported inside the function
            import httpx as _httpx_mod
            with patch.object(_httpx_mod, "Client", return_value=mock_client):
                return deliver_single_webhook_sync(**defaults)

    def test_successful_delivery(self):
        mock_client = self._make_httpx_mock(status_code=200)
        _, mock_ep, mock_sf = self._make_mock_session()
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["error"] is None

    def test_failed_delivery_http_error(self):
        mock_client = self._make_httpx_mock(status_code=500)
        _, mock_ep, mock_sf = self._make_mock_session(failure_count=2)
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is False
        assert result["status_code"] == 500
        assert "HTTP 500" in result["error"]

    def test_delivery_network_exception(self):
        mock_client = self._make_httpx_mock(side_effect=ConnectionError("Connection refused"))
        _, mock_ep, mock_sf = self._make_mock_session()
        result = self._run_delivery(mock_client, mock_sf, event_type="project.created")
        assert result["success"] is False
        assert result["status_code"] is None
        assert "Connection refused" in result["error"]

    def test_delivery_timeout_exception(self):
        import httpx as _httpx
        mock_client = self._make_httpx_mock(side_effect=_httpx.TimeoutException("Connection timed out"))
        _, mock_ep, mock_sf = self._make_mock_session()
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is False
        assert result["status_code"] is None
        assert "timed out" in result["error"].lower() or "Timeout" in result["error"]

    def test_delivery_sends_correct_headers(self):
        from app.services.webhook_dispatch import _sign_payload
        mock_client = self._make_httpx_mock(status_code=200)
        _, _, mock_sf = self._make_mock_session()
        payload = '{"event": "test"}'
        secret = "whsec_test"

        self._run_delivery(mock_client, mock_sf, payload_json=payload, secret=secret)

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers", call_kwargs[1].get("headers", {}))
        expected_sig = _sign_payload(payload, secret)
        assert headers["X-AO-Copilot-Signature"] == f"sha256={expected_sig}"
        assert headers["X-AO-Copilot-Event"] == "analysis.completed"
        assert headers["Content-Type"] == "application/json"

    def test_resets_failure_count_on_success(self):
        mock_client = self._make_httpx_mock(status_code=201)
        _, mock_ep, mock_sf = self._make_mock_session(failure_count=7)
        self._run_delivery(mock_client, mock_sf)
        assert mock_ep.failure_count == 0

    def test_increments_failure_count_on_failure(self):
        mock_client = self._make_httpx_mock(status_code=503)
        _, mock_ep, mock_sf = self._make_mock_session(failure_count=5)
        self._run_delivery(mock_client, mock_sf)
        assert mock_ep.failure_count == 6

    def test_endpoint_not_found_in_db(self):
        """If endpoint is not found in DB (ep is None), should not crash."""
        mock_client = self._make_httpx_mock(status_code=200)
        mock_session = MagicMock()
        mock_session.get.return_value = None  # endpoint not found
        mock_sf = MagicMock(return_value=mock_session)
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is True

    def test_http_299_is_success(self):
        """Any 2xx status should be treated as success."""
        mock_client = self._make_httpx_mock(status_code=299)
        _, mock_ep, mock_sf = self._make_mock_session(failure_count=3)
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is True
        assert mock_ep.failure_count == 0

    def test_http_300_is_failure(self):
        """300 is not 2xx, should be treated as failure."""
        mock_client = self._make_httpx_mock(status_code=300)
        _, mock_ep, mock_sf = self._make_mock_session()
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is False

    def test_error_message_truncated_at_500_chars(self):
        long_error = "x" * 1000
        mock_client = self._make_httpx_mock(side_effect=Exception(long_error))
        _, _, mock_sf = self._make_mock_session()
        result = self._run_delivery(mock_client, mock_sf)
        assert result["success"] is False
        assert len(result["error"]) <= 500


# ---------------------------------------------------------------------------
# get_subscribed_endpoints
# ---------------------------------------------------------------------------

class TestGetSubscribedEndpoints:
    @pytest.mark.asyncio
    async def test_returns_eligible_endpoints(self):
        from app.services.webhook_dispatch import get_subscribed_endpoints

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/webhook"
        mock_ep.secret = "whsec_abc"
        mock_ep.events = "analysis.completed, project.created"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ep]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
            endpoints = await get_subscribed_endpoints(
                mock_db, str(uuid.uuid4()), "analysis.completed"
            )

        assert len(endpoints) == 1
        assert endpoints[0]["url"] == "https://example.com/webhook"
        assert endpoints[0]["secret"] == "whsec_abc"

    @pytest.mark.asyncio
    async def test_filters_non_subscribed_events(self):
        from app.services.webhook_dispatch import get_subscribed_endpoints

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/webhook"
        mock_ep.secret = "whsec_abc"
        mock_ep.events = "project.created"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ep]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
            endpoints = await get_subscribed_endpoints(
                mock_db, str(uuid.uuid4()), "analysis.completed"
            )
        assert len(endpoints) == 0

    @pytest.mark.asyncio
    async def test_skips_unsafe_urls(self):
        from app.services.webhook_dispatch import get_subscribed_endpoints

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "http://localhost/evil"
        mock_ep.secret = "whsec_abc"
        mock_ep.events = "analysis.completed"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ep]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_dispatch._is_safe_url", return_value=False):
            endpoints = await get_subscribed_endpoints(
                mock_db, str(uuid.uuid4()), "analysis.completed"
            )
        assert len(endpoints) == 0

    @pytest.mark.asyncio
    async def test_fan_out_multiple_endpoints(self):
        from app.services.webhook_dispatch import get_subscribed_endpoints

        eps = []
        for i in range(3):
            mock_ep = MagicMock()
            mock_ep.id = uuid.uuid4()
            mock_ep.url = f"https://hook{i}.example.com/webhook"
            mock_ep.secret = f"whsec_{i}"
            mock_ep.events = "analysis.completed"
            eps.append(mock_ep)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = eps

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
            endpoints = await get_subscribed_endpoints(
                mock_db, str(uuid.uuid4()), "analysis.completed"
            )
        assert len(endpoints) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_match(self):
        from app.services.webhook_dispatch import get_subscribed_endpoints

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        endpoints = await get_subscribed_endpoints(mock_db, str(uuid.uuid4()), "quota.warning")
        assert endpoints == []

    @pytest.mark.asyncio
    async def test_whitespace_in_events_handled(self):
        """Events with spaces around commas should still match."""
        from app.services.webhook_dispatch import get_subscribed_endpoints

        mock_ep = MagicMock()
        mock_ep.id = uuid.uuid4()
        mock_ep.url = "https://example.com/hook"
        mock_ep.secret = "s"
        mock_ep.events = "  analysis.completed ,  export.completed  "

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ep]
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_dispatch._is_safe_url", return_value=True):
            endpoints = await get_subscribed_endpoints(
                mock_db, str(uuid.uuid4()), "analysis.completed"
            )
        assert len(endpoints) == 1


# ---------------------------------------------------------------------------
# dispatch_event (legacy async)
# ---------------------------------------------------------------------------

class TestDispatchEvent:
    @pytest.mark.asyncio
    async def test_dispatch_no_endpoints(self):
        from app.services.webhook_dispatch import dispatch_event

        mock_db = AsyncMock()
        with patch("app.services.webhook_dispatch.get_subscribed_endpoints", return_value=[]):
            count = await dispatch_event(mock_db, "org-1", "analysis.completed", {"project_id": "p1"})
        assert count == 0

    @pytest.mark.asyncio
    async def test_dispatch_success_count(self):
        from app.services.webhook_dispatch import dispatch_event

        mock_db = AsyncMock()
        endpoints = [
            {"endpoint_id": str(uuid.uuid4()), "url": "https://hook1.com", "secret": "s1"},
            {"endpoint_id": str(uuid.uuid4()), "url": "https://hook2.com", "secret": "s2"},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.webhook_dispatch.get_subscribed_endpoints", return_value=endpoints), \
             patch("app.services.webhook_dispatch.httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.webhook_dispatch.WebhookDelivery"):
            count = await dispatch_event(mock_db, "org-1", "analysis.completed", {"project_id": "p1"})
        assert count == 2

    @pytest.mark.asyncio
    async def test_dispatch_all_fail_with_exception(self):
        from app.services.webhook_dispatch import dispatch_event

        mock_db = AsyncMock()
        endpoints = [
            {"endpoint_id": str(uuid.uuid4()), "url": "https://hook1.com", "secret": "s1"},
        ]

        mock_client = AsyncMock()
        mock_client.post.side_effect = ConnectionError("refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.webhook_dispatch.get_subscribed_endpoints", return_value=endpoints), \
             patch("app.services.webhook_dispatch.httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.webhook_dispatch.WebhookDelivery"):
            count = await dispatch_event(mock_db, "org-1", "test.event", {})
        assert count == 0

    @pytest.mark.asyncio
    async def test_dispatch_with_500_response(self):
        from app.services.webhook_dispatch import dispatch_event

        mock_db = AsyncMock()
        endpoints = [
            {"endpoint_id": str(uuid.uuid4()), "url": "https://hook1.com", "secret": "s1"},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.webhook_dispatch.get_subscribed_endpoints", return_value=endpoints), \
             patch("app.services.webhook_dispatch.httpx.AsyncClient", return_value=mock_client), \
             patch("app.services.webhook_dispatch.WebhookDelivery"):
            count = await dispatch_event(mock_db, "org-1", "test.event", {})
        assert count == 0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_webhook_timeout(self):
        from app.services.webhook_dispatch import WEBHOOK_TIMEOUT
        assert WEBHOOK_TIMEOUT == 10

    def test_max_failure_count(self):
        from app.services.webhook_dispatch import MAX_FAILURE_COUNT
        assert MAX_FAILURE_COUNT == 10
