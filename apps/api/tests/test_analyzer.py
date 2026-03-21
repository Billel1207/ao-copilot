"""Tests pour app/services/analyzer.py — orchestration pipeline IA.

Teste les fonctions pures et les helpers sans dépendance DB/LLM,
et les fonctions avec DB mockée.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

from app.services.analyzer import (
    check_dce_completeness,
    _CRITICAL_DOC_TYPES,
    _IMPORTANT_DOC_TYPES,
    MIN_RAG_SIMILARITY,
    SUMMARY_QUERY,
    CHECKLIST_QUERY,
    CRITERIA_QUERY,
    GONOGO_QUERY,
    DEADLINE_QUERY,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalyzerConstants:
    def test_critical_doc_types(self):
        assert "RC" in _CRITICAL_DOC_TYPES
        assert "CCTP" in _CRITICAL_DOC_TYPES

    def test_important_doc_types(self):
        assert "CCAP" in _IMPORTANT_DOC_TYPES
        assert "DPGF" in _IMPORTANT_DOC_TYPES

    def test_rag_similarity_threshold(self):
        assert 0.0 < MIN_RAG_SIMILARITY < 1.0

    def test_query_strings_non_empty(self):
        for q in (SUMMARY_QUERY, CHECKLIST_QUERY, CRITERIA_QUERY, GONOGO_QUERY, DEADLINE_QUERY):
            assert isinstance(q, str) and len(q) > 10


# ═══════════════════════════════════════════════════════════════════════════════
# check_dce_completeness
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class FakeDoc:
    doc_type: str


class TestCheckDceCompleteness:
    def _mock_db(self, doc_types: list[str]):
        """Create a mock DB session that returns docs with given types."""
        docs = [FakeDoc(doc_type=t) for t in doc_types]
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = docs
        mock_query.filter_by.return_value = mock_filter
        mock_db.query.return_value = mock_query
        return mock_db

    def test_complete_dce(self):
        db = self._mock_db(["RC", "CCTP", "CCAP", "DPGF"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is True
        assert result["missing_critical"] == []
        assert result["doc_count"] == 4

    def test_missing_critical_rc(self):
        db = self._mock_db(["CCTP", "CCAP"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is False
        assert "RC" in result["missing_critical"]

    def test_missing_critical_cctp(self):
        db = self._mock_db(["RC", "CCAP"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is False
        assert "CCTP" in result["missing_critical"]

    def test_missing_important(self):
        db = self._mock_db(["RC", "CCTP"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is True
        assert len(result["missing_important"]) > 0

    def test_empty_dce(self):
        db = self._mock_db([])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is False
        assert result["doc_count"] == 0
        assert any("Aucun document" in w for w in result["warnings"])

    def test_single_doc_warning(self):
        db = self._mock_db(["RC"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert any("seul document" in w.lower() for w in result["warnings"])

    def test_present_types_sorted(self):
        db = self._mock_db(["DPGF", "RC", "CCTP", "CCAP"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["present_types"] == sorted(result["present_types"])

    def test_warnings_contain_label(self):
        db = self._mock_db(["CCAP"])  # Missing RC and CCTP
        result = check_dce_completeness(db, str(uuid.uuid4()))
        warning_text = " ".join(result["warnings"])
        assert "Règlement de Consultation" in warning_text or "RC" in warning_text

    def test_full_dce_no_warnings(self):
        db = self._mock_db(["RC", "CCTP", "CCAP", "DPGF", "BPU", "AE"])
        result = check_dce_completeness(db, str(uuid.uuid4()))
        assert result["is_complete"] is True
        assert result["missing_critical"] == []
        assert result["missing_important"] == []

    def test_doc_with_none_type_ignored(self):
        docs = [FakeDoc(doc_type="RC"), FakeDoc(doc_type=None), FakeDoc(doc_type="CCTP")]
        mock_db = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = docs
        mock_db.query.return_value.filter_by.return_value = mock_filter
        result = check_dce_completeness(mock_db, str(uuid.uuid4()))
        assert result["doc_count"] == 3
        assert result["is_complete"] is True  # RC + CCTP present
