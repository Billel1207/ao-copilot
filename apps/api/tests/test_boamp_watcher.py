"""Tests for app.services.boamp_watcher — BOAMP API tender monitoring."""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.services.boamp_watcher import (
    _build_query_params,
    _parse_date,
    _parse_value,
    _normalize_record,
    fetch_boamp_results,
    BOAMP_API_URL,
)


# ---------------------------------------------------------------------------
# Helpers — mock AoWatchConfig
# ---------------------------------------------------------------------------

def _make_config(**kwargs):
    """Create a mock AoWatchConfig for testing."""
    config = MagicMock()
    config.org_id = kwargs.get("org_id", uuid.uuid4())
    config.keywords = kwargs.get("keywords", [])
    config.regions = kwargs.get("regions", [])
    config.cpv_codes = kwargs.get("cpv_codes", [])
    config.min_budget_eur = kwargs.get("min_budget_eur", None)
    config.max_budget_eur = kwargs.get("max_budget_eur", None)
    config.is_active = kwargs.get("is_active", True)
    config.last_checked_at = None
    return config


# ---------------------------------------------------------------------------
# _build_query_params
# ---------------------------------------------------------------------------

class TestBuildQueryParams:
    def test_empty_config(self):
        config = _make_config()
        params = _build_query_params(config)
        assert params["limit"] == 100
        assert params["order_by"] == "dateparution desc"
        assert "where" not in params

    def test_with_keywords(self):
        config = _make_config(keywords=["construction", "renovation"])
        params = _build_query_params(config)
        assert "where" in params
        assert 'search(objet, "construction")' in params["where"]
        assert 'search(objet, "renovation")' in params["where"]
        assert " OR " in params["where"]

    def test_with_regions(self):
        config = _make_config(regions=["Paris", "Lyon"])
        params = _build_query_params(config)
        assert "where" in params
        assert 'search(lieu, "Paris")' in params["where"]

    def test_with_cpv_codes(self):
        config = _make_config(cpv_codes=["45000000", "71000000"])
        params = _build_query_params(config)
        assert "where" in params
        assert 'search(cpv, "45000000")' in params["where"]

    def test_combined_filters(self):
        config = _make_config(keywords=["btp"], regions=["Paris"], cpv_codes=["45000000"])
        params = _build_query_params(config)
        where = params["where"]
        assert " AND " in where  # All 3 groups ANDed together


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_iso_format(self):
        dt = _parse_date("2026-04-01T10:00:00+0200")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 4

    def test_date_only(self):
        dt = _parse_date("2026-04-01")
        assert dt is not None
        assert dt.day == 1

    def test_french_format(self):
        dt = _parse_date("01/04/2026")
        assert dt is not None
        assert dt.year == 2026

    def test_none_input(self):
        assert _parse_date(None) is None

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_invalid_format(self):
        assert _parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# _parse_value
# ---------------------------------------------------------------------------

class TestParseValue:
    def test_integer(self):
        assert _parse_value("500000") == 500000

    def test_float_string(self):
        assert _parse_value("1234567.89") == 1234567

    def test_comma_float(self):
        assert _parse_value("1 234,56") == 1234

    def test_none(self):
        assert _parse_value(None) is None

    def test_invalid(self):
        assert _parse_value("abc") is None

    def test_numeric_type(self):
        assert _parse_value(50000) == 50000


# ---------------------------------------------------------------------------
# _normalize_record
# ---------------------------------------------------------------------------

class TestNormalizeRecord:
    def test_standard_record(self):
        record = {
            "fields": {
                "idweb": "BOAMP-123",
                "objet": "Construction gymnasium",
                "nomacheteur": "Mairie de Paris",
                "lieu": "Paris",
                "dateparution": "2026-03-15",
                "datelimitereponse": "2026-04-15",
                "valeurestimee": "500000",
                "procedure": "Appel d'offres ouvert",
                "cpv": "45000000,71000000",
                "urlannonce": "https://www.boamp.fr/avis/detail/BOAMP-123",
            }
        }
        result = _normalize_record(record)
        assert result["boamp_ref"] == "BOAMP-123"
        assert result["title"] == "Construction gymnasium"
        assert result["buyer"] == "Mairie de Paris"
        assert result["cpv_codes"] == ["45000000", "71000000"]
        assert result["estimated_value_eur"] == 500000

    def test_cpv_as_list(self):
        record = {"fields": {"cpv": ["45000000", "71000000"], "objet": "Test"}}
        result = _normalize_record(record)
        assert result["cpv_codes"] == ["45000000", "71000000"]

    def test_missing_fields_use_defaults(self):
        record = {"fields": {"objet": "Minimal tender"}}
        result = _normalize_record(record)
        assert result["title"] == "Minimal tender"
        assert result["buyer"] is None
        assert result["region"] is None

    def test_empty_fields(self):
        record = {"fields": {}}
        result = _normalize_record(record)
        assert result["title"] == "Sans titre"

    def test_record_id_as_fallback_ref(self):
        record = {"record_id": "rec-456", "fields": {"objet": "Test"}}
        result = _normalize_record(record)
        assert result["boamp_ref"] == "rec-456"

    def test_title_truncated(self):
        record = {"fields": {"objet": "A" * 2000}}
        result = _normalize_record(record)
        assert len(result["title"]) <= 1000

    def test_alternative_field_names(self):
        record = {"fields": {
            "reference": "REF-001",
            "intitule": "Alt title",
            "acheteur": "Alt buyer",
            "region": "Alt region",
            "date_publication": "2026-01-01",
            "date_limite_reponse": "2026-02-01",
            "valeur_estimee": "100000",
            "typemarche": "Marche public",
            "codeCPV": ["45000000"],
            "url": "https://example.com",
        }}
        result = _normalize_record(record)
        assert result["boamp_ref"] == "REF-001"
        assert result["title"] == "Alt title"
        assert result["buyer"] == "Alt buyer"


# ---------------------------------------------------------------------------
# fetch_boamp_results — with mocked httpx
# ---------------------------------------------------------------------------

class TestFetchBoampResults:
    @patch("app.services.boamp_watcher.httpx.Client")
    def test_successful_fetch(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"fields": {
                    "idweb": "BOAMP-001",
                    "objet": "Construction batiment",
                    "valeurestimee": "300000",
                }},
                {"fields": {
                    "idweb": "BOAMP-002",
                    "objet": "Renovation ecole",
                    "valeurestimee": "150000",
                }},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config(keywords=["construction"])
        results = fetch_boamp_results(config)
        assert len(results) == 2
        assert results[0]["boamp_ref"] == "BOAMP-001"

    @patch("app.services.boamp_watcher.httpx.Client")
    def test_budget_filter_min(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"fields": {"idweb": "B1", "objet": "Small", "valeurestimee": "50000"}},
                {"fields": {"idweb": "B2", "objet": "Big", "valeurestimee": "500000"}},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config(min_budget_eur=100000)
        results = fetch_boamp_results(config)
        assert len(results) == 1
        assert results[0]["boamp_ref"] == "B2"

    @patch("app.services.boamp_watcher.httpx.Client")
    def test_budget_filter_max(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"fields": {"idweb": "B1", "objet": "Small", "valeurestimee": "50000"}},
                {"fields": {"idweb": "B2", "objet": "Big", "valeurestimee": "500000"}},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config(max_budget_eur=100000)
        results = fetch_boamp_results(config)
        assert len(results) == 1
        assert results[0]["boamp_ref"] == "B1"

    @patch("app.services.boamp_watcher.httpx")
    def test_timeout_returns_empty(self, mock_httpx):
        import httpx
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_httpx.Client.return_value = mock_client
        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError

        config = _make_config()
        results = fetch_boamp_results(config)
        assert results == []

    @patch("app.services.boamp_watcher.httpx")
    def test_http_error_returns_empty(self, mock_httpx):
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        error = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.get.side_effect = error
        mock_httpx.Client.return_value = mock_client
        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError

        config = _make_config()
        results = fetch_boamp_results(config)
        assert results == []

    @patch("app.services.boamp_watcher.httpx.Client")
    def test_empty_results(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config()
        results = fetch_boamp_results(config)
        assert results == []

    @patch("app.services.boamp_watcher.httpx.Client")
    def test_malformed_record_skipped(self, mock_client_cls):
        """Records that fail normalization should be silently skipped."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"fields": {"idweb": "OK", "objet": "Valid"}},
                "not_a_dict",  # Will cause exception in _normalize_record
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config()
        results = fetch_boamp_results(config)
        # At least the valid record should be there
        assert len(results) >= 1

    @patch("app.services.boamp_watcher.httpx.Client")
    def test_alternative_data_key(self, mock_client_cls):
        """API may return 'records' instead of 'results'."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "records": [
                {"fields": {"idweb": "REC-1", "objet": "Via records key"}},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        config = _make_config()
        results = fetch_boamp_results(config)
        assert len(results) == 1
        assert results[0]["boamp_ref"] == "REC-1"
