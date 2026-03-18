"""Tests pour app/services/export_data.py — DictObj, _fetch_result, fetch_export_data."""
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.export_data import DictObj, _fetch_result, fetch_export_data, ExportData


# ── DictObj ──────────────────────────────────────────────────────────────────


class TestDictObj:
    def test_simple_dict_access(self):
        obj = DictObj({"name": "Alice", "age": 30})
        assert obj.name == "Alice"
        assert obj.age == 30

    def test_nested_dict_becomes_dictobj(self):
        obj = DictObj({"inner": {"key": "value"}})
        assert isinstance(obj.inner, DictObj)
        assert obj.inner.key == "value"

    def test_list_of_dicts_becomes_list_of_dictobj(self):
        obj = DictObj({"items": [{"a": 1}, {"b": 2}]})
        assert isinstance(obj.items, list)
        assert len(obj.items) == 2
        assert isinstance(obj.items[0], DictObj)
        assert obj.items[0].a == 1
        assert obj.items[1].b == 2

    def test_missing_attr_returns_none(self):
        obj = DictObj({"x": 1})
        assert obj.nonexistent is None

    def test_underscore_attr_raises(self):
        obj = DictObj({"x": 1})
        with pytest.raises(AttributeError):
            _ = obj._private

    def test_bool_is_true(self):
        obj = DictObj({})
        assert bool(obj) is True

    def test_len_is_zero(self):
        obj = DictObj({"a": 1})
        assert len(obj) == 0

    def test_iter_is_empty(self):
        obj = DictObj({"a": 1})
        assert list(obj) == []

    def test_none_input_creates_valid_empty_obj(self):
        obj = DictObj(None)
        assert bool(obj) is True
        assert obj.anything is None

    def test_list_with_non_dict_items(self):
        obj = DictObj({"tags": ["a", "b", 3]})
        assert obj.tags == ["a", "b", 3]


# ── _fetch_result ────────────────────────────────────────────────────────────


class TestFetchResult:
    def _make_mock_db(self, results_by_type: dict):
        """Helper: builds a mock db.query(...) chain.

        results_by_type: {"summary": mock_obj, "rc": None, ...}
        """
        db = MagicMock()

        def query_side_effect(*args, **kwargs):
            q = MagicMock()

            def filter_by_side(**kw):
                rtype = kw.get("result_type")
                f = MagicMock()

                def order_by_side(*a, **k):
                    o = MagicMock()
                    o.first.return_value = results_by_type.get(rtype)
                    return o

                f.order_by = order_by_side
                return f

            q.filter_by = filter_by_side
            return q

        db.query.side_effect = query_side_effect
        return db

    def test_returns_primary_type(self):
        expected = MagicMock(payload={"key": "val"})
        db = self._make_mock_db({"summary": expected})
        pid = uuid.uuid4()
        result = _fetch_result(db, pid, "summary", "summary_v2")
        assert result is expected

    def test_fallback_to_second_type(self):
        expected = MagicMock(payload={"fallback": True})
        db = self._make_mock_db({"rc": expected})
        pid = uuid.uuid4()
        result = _fetch_result(db, pid, "rc_analysis", "rc")
        assert result is expected

    def test_no_result_returns_none(self):
        db = self._make_mock_db({})
        pid = uuid.uuid4()
        result = _fetch_result(db, pid, "missing", "also_missing")
        assert result is None


# ── fetch_export_data ────────────────────────────────────────────────────────


class TestFetchExportData:
    def _build_mock_db(self, project=None, documents=None, extraction_results=None,
                       checklist_items=None):
        """Build a mock DB session for fetch_export_data."""
        db = MagicMock()
        extraction_results = extraction_results or {}
        documents = documents or []
        checklist_items = checklist_items or []

        from app.models.project import AoProject
        from app.models.document import AoDocument
        from app.models.analysis import ExtractionResult, ChecklistItem

        def query_side_effect(model):
            q = MagicMock()

            if model is AoProject:
                fb = MagicMock()
                fb.first.return_value = project
                q.filter_by = MagicMock(return_value=fb)

            elif model is AoDocument:
                fb = MagicMock()
                fb.all.return_value = documents
                q.filter_by = MagicMock(return_value=fb)

            elif model is ExtractionResult:
                def filter_by_side(**kw):
                    rtype = kw.get("result_type")
                    f = MagicMock()

                    def order_by_side(*a, **k):
                        o = MagicMock()
                        o.first.return_value = extraction_results.get(rtype)
                        return o

                    f.order_by = order_by_side
                    return f

                q.filter_by = filter_by_side

            elif model is ChecklistItem:
                def filter_by_cl(**kw):
                    f = MagicMock()

                    def order_by_cl(*a, **k):
                        o = MagicMock()
                        o.all.return_value = checklist_items
                        return o

                    f.order_by = order_by_cl
                    return f

                q.filter_by = filter_by_cl

            return q

        db.query.side_effect = query_side_effect
        return db

    def test_project_not_found_raises_valueerror(self):
        db = self._build_mock_db(project=None)
        with pytest.raises(ValueError, match="introuvable"):
            fetch_export_data(db, str(uuid.uuid4()))

    @patch("app.services.export_data.DictObj", wraps=DictObj)
    def test_project_found_returns_export_data(self, _):
        project = MagicMock()
        project.title = "Test AO"
        pid = uuid.uuid4()

        summary_r = MagicMock()
        summary_r.payload = {
            "confidence_overall": 0.87,
            "project_overview": {"deadline_submission": "2099-12-31"},
        }

        db = self._build_mock_db(
            project=project,
            extraction_results={"summary": summary_r},
        )

        result = fetch_export_data(db, str(pid))

        assert isinstance(result, ExportData)
        assert result.project is project
        assert result.confidence == 0.87

    def test_checklist_stats_computed(self):
        project = MagicMock()
        pid = uuid.uuid4()

        items = []
        for crit, status in [("Eliminatoire", "MANQUANT"), ("Important", "OK"),
                              ("Info", "OK"), ("Eliminatoire", "OK")]:
            item = MagicMock()
            item.criticality = crit
            item.status = status
            items.append(item)

        db = self._build_mock_db(project=project, checklist_items=items)

        result = fetch_export_data(db, str(pid))

        assert result.checklist_stats["eliminatoire"] == 2
        assert result.checklist_stats["important"] == 1
        assert result.checklist_stats["info"] == 1
        assert result.checklist_stats["ok"] == 3

    def test_days_remaining_from_summary_deadline(self):
        project = MagicMock()
        pid = uuid.uuid4()

        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        summary_r = MagicMock()
        summary_r.payload = {
            "project_overview": {"deadline_submission": future},
        }

        db = self._build_mock_db(
            project=project,
            extraction_results={"summary": summary_r},
        )

        result = fetch_export_data(db, str(pid))

        # Should be approximately 29 or 30 days
        assert result.days_remaining is not None
        assert 28 <= result.days_remaining <= 30

    def test_confidence_from_summary_fallback_key(self):
        project = MagicMock()
        pid = uuid.uuid4()

        summary_r = MagicMock()
        summary_r.payload = {"confidence": 0.72}

        db = self._build_mock_db(
            project=project,
            extraction_results={"summary": summary_r},
        )

        result = fetch_export_data(db, str(pid))
        assert result.confidence == 0.72
