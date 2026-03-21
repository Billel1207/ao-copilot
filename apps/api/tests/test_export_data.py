"""Tests for app.services.export_data — DictObj, ExportData, helpers."""
import uuid
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import fields

from app.services.export_data import DictObj, ExportData


class TestDictObj:
    """Test DictObj attribute-access wrapper."""

    def test_basic_attribute_access(self):
        obj = DictObj({"name": "test", "value": 42})
        assert obj.name == "test"
        assert obj.value == 42

    def test_missing_attribute_returns_none(self):
        obj = DictObj({"name": "test"})
        assert obj.missing_key is None

    def test_nested_dict_becomes_dictobj(self):
        obj = DictObj({"inner": {"a": 1, "b": 2}})
        assert isinstance(obj.inner, DictObj)
        assert obj.inner.a == 1
        assert obj.inner.b == 2

    def test_list_of_dicts(self):
        obj = DictObj({"items": [{"x": 1}, {"x": 2}]})
        assert len(obj.items) == 2
        assert isinstance(obj.items[0], DictObj)
        assert obj.items[0].x == 1
        assert obj.items[1].x == 2

    def test_list_of_non_dicts(self):
        obj = DictObj({"tags": ["a", "b", "c"]})
        assert obj.tags == ["a", "b", "c"]

    def test_mixed_list(self):
        obj = DictObj({"data": [{"k": "v"}, "plain", 42]})
        assert isinstance(obj.data[0], DictObj)
        assert obj.data[0].k == "v"
        assert obj.data[1] == "plain"
        assert obj.data[2] == 42

    def test_none_input(self):
        obj = DictObj(None)
        assert obj.anything is None

    def test_non_dict_input_string(self):
        obj = DictObj("not a dict")
        assert obj.anything is None

    def test_non_dict_input_int(self):
        obj = DictObj(123)
        assert obj.foo is None

    def test_non_dict_input_list(self):
        obj = DictObj([1, 2, 3])
        assert obj.foo is None

    def test_empty_dict(self):
        obj = DictObj({})
        assert obj.anything is None

    def test_bool_always_true(self):
        assert bool(DictObj(None)) is True
        assert bool(DictObj({})) is True
        assert bool(DictObj({"a": 1})) is True

    def test_iter_returns_empty(self):
        obj = DictObj({"a": 1})
        assert list(obj) == []

    def test_len_returns_zero(self):
        obj = DictObj({"a": 1})
        assert len(obj) == 0

    def test_private_attr_raises(self):
        obj = DictObj({"a": 1})
        with pytest.raises(AttributeError):
            _ = obj._private

    def test_dunder_attr_raises(self):
        obj = DictObj({"a": 1})
        with pytest.raises(AttributeError):
            _ = obj.__secret

    def test_keys_tracked(self):
        obj = DictObj({"x": 1, "y": 2})
        assert "x" in obj._keys
        assert "y" in obj._keys

    def test_deeply_nested(self):
        obj = DictObj({"a": {"b": {"c": {"d": "deep"}}}})
        assert obj.a.b.c.d == "deep"

    def test_deeply_nested_missing(self):
        obj = DictObj({"a": {"b": 1}})
        # obj.a.c is None, accessing .d on None would fail
        # but obj.a.missing returns None (not DictObj)
        assert obj.a.missing is None

    def test_boolean_values(self):
        obj = DictObj({"flag": True, "off": False})
        assert obj.flag is True
        assert obj.off is False

    def test_none_value_in_dict(self):
        obj = DictObj({"key": None})
        assert obj.key is None

    def test_empty_list_value(self):
        obj = DictObj({"items": []})
        assert obj.items == []

    def test_nested_list_of_dicts_in_dict(self):
        obj = DictObj({"outer": {"inner_list": [{"val": 10}]}})
        assert isinstance(obj.outer, DictObj)
        assert isinstance(obj.outer.inner_list[0], DictObj)
        assert obj.outer.inner_list[0].val == 10


class TestExportData:
    """Test ExportData dataclass defaults."""

    def test_default_checklist_stats(self):
        mock_project = MagicMock()
        data = ExportData(project=mock_project)
        assert data.checklist_stats == {
            "eliminatoire": 0, "important": 0, "info": 0, "ok": 0
        }

    def test_default_lists_empty(self):
        mock_project = MagicMock()
        data = ExportData(project=mock_project)
        assert data.documents == []
        assert data.checklist_items == []

    def test_default_none_fields(self):
        mock_project = MagicMock()
        data = ExportData(project=mock_project)
        assert data.summary is None
        assert data.criteria is None
        assert data.gonogo is None
        assert data.timeline is None
        assert data.confidence is None
        assert data.days_remaining is None
        assert data.deadline_str is None
        assert data.gonogo_obj is None
        assert data.timeline_obj is None

    def test_all_analysis_fields_none_by_default(self):
        mock_project = MagicMock()
        data = ExportData(project=mock_project)
        analysis_fields = [
            "ccap_analysis", "ccag_derogations", "ccap_clauses_risquees",
            "rc_analysis", "ae_analysis", "cctp_analysis", "dc_check",
            "conflicts", "cashflow", "subcontracting", "questions",
            "scoring", "dpgf_pricing", "glossaire_btp",
        ]
        for f_name in analysis_fields:
            assert getattr(data, f_name) is None, f"{f_name} should be None"

    def test_checklist_stats_independent_instances(self):
        """Each ExportData should have its own checklist_stats dict."""
        p = MagicMock()
        d1 = ExportData(project=p)
        d2 = ExportData(project=p)
        d1.checklist_stats["ok"] = 5
        assert d2.checklist_stats["ok"] == 0
