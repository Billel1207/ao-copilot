"""Tests for app/services/analyzer.py — full pipeline orchestration.

Covers:
- run_full_analysis success / error paths
- check_dce_completeness
- _save_result, _save_checklist_items, _save_criteria_items
- _extract_and_save_deadlines
- _parse_montant
- _get_doc_text_by_type, _get_all_doc_text, _get_all_doc_texts_by_type
- _get_company_profile_dict, _get_avg_ocr_quality
- _run_in_thread
- ThreadPoolExecutor batch execution
- Batch 3 sequential steps (scoring, cashflow, subcontracting)
- Error handling / Sentry reporting
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

# ── Module path constants ────────────────────────────────────────────────────
MOD = "app.services.analyzer"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_mock_db():
    """Create a MagicMock that behaves like a SQLAlchemy Session."""
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    db.query.return_value.filter_by.return_value.all.return_value = []
    db.query.return_value.filter_by.return_value.delete.return_value = 0
    return db


def _project_id():
    return str(uuid.uuid4())


def _fake_chunks():
    return [
        {"text": "chunk1 text content", "score": 0.90, "doc_type": "RC"},
        {"text": "chunk2 more text", "score": 0.85, "doc_type": "CCTP"},
    ]


def _mock_project(org_id=None):
    p = MagicMock()
    p.org_id = org_id or uuid.uuid4()
    return p


# ═════════════════════════════════════════════════════════════════════════════
# 1. _parse_montant
# ═════════════════════════════════════════════════════════════════════════════

class TestParseMontant:
    def test_none(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant(None) is None

    def test_int(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant(42) == 42.0

    def test_float(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant(3.14) == 3.14

    def test_string_with_currency(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant("1 331 418,00 €") == 1331418.0

    def test_invalid_string(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant("not a number") is None

    def test_string_plain(self):
        from app.services.analyzer import _parse_montant
        assert _parse_montant("500000") == 500000.0


# ═════════════════════════════════════════════════════════════════════════════
# 2. check_dce_completeness
# ═════════════════════════════════════════════════════════════════════════════

class TestCheckDceCompleteness:
    def test_empty_docs(self):
        from app.services.analyzer import check_dce_completeness
        db = _make_mock_db()
        db.query.return_value.filter_by.return_value.all.return_value = []
        result = check_dce_completeness(db, _project_id())
        assert result["is_complete"] is False
        assert result["doc_count"] == 0
        assert len(result["warnings"]) >= 1

    def test_complete_dce(self):
        from app.services.analyzer import check_dce_completeness
        db = _make_mock_db()
        docs = []
        for dtype in ("RC", "CCTP", "CCAP", "DPGF", "BPU"):
            d = MagicMock()
            d.doc_type = dtype
            docs.append(d)
        db.query.return_value.filter_by.return_value.all.return_value = docs
        result = check_dce_completeness(db, _project_id())
        assert result["is_complete"] is True
        assert result["missing_critical"] == []
        assert result["missing_important"] == []
        assert result["doc_count"] == 5

    def test_missing_critical(self):
        from app.services.analyzer import check_dce_completeness
        db = _make_mock_db()
        d = MagicMock()
        d.doc_type = "CCAP"
        db.query.return_value.filter_by.return_value.all.return_value = [d]
        result = check_dce_completeness(db, _project_id())
        assert result["is_complete"] is False
        assert "RC" in result["missing_critical"] or "CCTP" in result["missing_critical"]

    def test_single_doc_warning(self):
        from app.services.analyzer import check_dce_completeness
        db = _make_mock_db()
        d = MagicMock()
        d.doc_type = "RC"
        db.query.return_value.filter_by.return_value.all.return_value = [d]
        result = check_dce_completeness(db, _project_id())
        assert any("Un seul document" in w for w in result["warnings"])


# ═════════════════════════════════════════════════════════════════════════════
# 3. _save_result
# ═════════════════════════════════════════════════════════════════════════════

class TestSaveResult:
    @patch(f"{MOD}.llm_service")
    def test_creates_new_result(self, mock_llm):
        from app.services.analyzer import _save_result
        mock_llm.get_model_name.return_value = "claude-test"
        db = _make_mock_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        _save_result(db, _project_id(), "summary", {"key": "val"}, confidence=0.9)
        db.add.assert_called_once()

    @patch(f"{MOD}.llm_service")
    def test_updates_existing_result(self, mock_llm):
        from app.services.analyzer import _save_result
        mock_llm.get_model_name.return_value = "claude-test"
        db = _make_mock_db()
        existing = MagicMock()
        existing.version = 1
        db.query.return_value.filter_by.return_value.first.return_value = existing
        _save_result(db, _project_id(), "summary", {"key": "val2"}, confidence=0.8)
        assert existing.payload == {"key": "val2"}
        assert existing.confidence == 0.8
        assert existing.version == 2
        db.add.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# 4. _save_checklist_items
# ═════════════════════════════════════════════════════════════════════════════

class TestSaveChecklistItems:
    def test_saves_items(self):
        from app.services.analyzer import _save_checklist_items
        db = _make_mock_db()
        items = [
            {"category": "Admin", "requirement": "DC1", "criticality": "Éliminatoire",
             "status": "MANQUANT", "what_to_provide": "DC1 signé", "citations": [], "confidence": 0.9},
        ]
        _save_checklist_items(db, _project_id(), items)
        db.query.return_value.filter_by.return_value.delete.assert_called_once()
        assert db.add.call_count == 1

    def test_empty_items(self):
        from app.services.analyzer import _save_checklist_items
        db = _make_mock_db()
        _save_checklist_items(db, _project_id(), [])
        db.query.return_value.filter_by.return_value.delete.assert_called_once()
        db.add.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# 5. _save_criteria_items
# ═════════════════════════════════════════════════════════════════════════════

class TestSaveCriteriaItems:
    def test_saves_eligibility_and_scoring(self):
        from app.services.analyzer import _save_criteria_items
        db = _make_mock_db()
        evaluation = {
            "eligibility_conditions": [
                {"condition": "CA > 1M", "type": "hard", "citations": []},
            ],
            "scoring_criteria": [
                {"criterion": "Prix", "weight_percent": 60, "notes": "note", "citations": []},
            ],
        }
        _save_criteria_items(db, _project_id(), evaluation)
        assert db.add.call_count == 2


# ═════════════════════════════════════════════════════════════════════════════
# 6. _extract_and_save_deadlines
# ═════════════════════════════════════════════════════════════════════════════

class TestExtractAndSaveDeadlines:
    def test_saves_from_timeline_payload(self):
        from app.services.analyzer import _extract_and_save_deadlines
        db = _make_mock_db()
        timeline = {
            "submission_deadline": "2026-04-01T12:00:00+02:00",
            "site_visit_date": "2026-03-15T10:00:00Z",
            "key_dates": [],
        }
        _extract_and_save_deadlines(db, _project_id(), timeline)
        assert db.add.call_count == 2

    def test_invalid_date_skipped(self):
        from app.services.analyzer import _extract_and_save_deadlines
        db = _make_mock_db()
        timeline = {
            "submission_deadline": "not-a-date",
            "key_dates": [],
        }
        _extract_and_save_deadlines(db, _project_id(), timeline)
        db.add.assert_not_called()

    def test_key_dates_classification(self):
        from app.services.analyzer import _extract_and_save_deadlines
        db = _make_mock_db()
        timeline = {
            "key_dates": [
                {"date": "2026-04-01T12:00:00Z", "label": "Date remise des offres", "mandatory": True},
                {"date": "2026-03-20T09:00:00Z", "label": "Visite de site obligatoire", "mandatory": False},
                {"date": "2026-05-01T00:00:00Z", "label": "Publication résultats", "mandatory": False},
            ],
        }
        _extract_and_save_deadlines(db, _project_id(), timeline)
        assert db.add.call_count == 3


# ═════════════════════════════════════════════════════════════════════════════
# 7. _get_avg_ocr_quality
# ═════════════════════════════════════════════════════════════════════════════

class TestGetAvgOcrQuality:
    def test_no_docs(self):
        from app.services.analyzer import _get_avg_ocr_quality
        db = _make_mock_db()
        db.query.return_value.filter_by.return_value.all.return_value = []
        assert _get_avg_ocr_quality(db, _project_id()) is None

    def test_no_scores(self):
        from app.services.analyzer import _get_avg_ocr_quality
        db = _make_mock_db()
        d = MagicMock()
        d.ocr_quality_score = None
        db.query.return_value.filter_by.return_value.all.return_value = [d]
        assert _get_avg_ocr_quality(db, _project_id()) is None

    def test_average_calculation(self):
        from app.services.analyzer import _get_avg_ocr_quality
        db = _make_mock_db()
        d1 = MagicMock(); d1.ocr_quality_score = 80
        d2 = MagicMock(); d2.ocr_quality_score = 90
        db.query.return_value.filter_by.return_value.all.return_value = [d1, d2]
        assert _get_avg_ocr_quality(db, _project_id()) == 85.0


# ═════════════════════════════════════════════════════════════════════════════
# 8. _run_in_thread
# ═════════════════════════════════════════════════════════════════════════════

class TestRunInThread:
    @patch(f"{MOD}.SyncSessionLocal")
    def test_success(self, mock_session_cls):
        from app.services.analyzer import _run_in_thread
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        result_data = {"hello": "world"}
        step_fn = MagicMock(return_value=result_data)

        name, result = _run_in_thread(step_fn, "test_step", "pid123")
        assert name == "test_step"
        assert result == result_data
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch(f"{MOD}._report_to_sentry")
    @patch(f"{MOD}.SyncSessionLocal")
    def test_exception_returns_none(self, mock_session_cls, mock_sentry):
        from app.services.analyzer import _run_in_thread
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        step_fn = MagicMock(side_effect=RuntimeError("boom"))

        name, result = _run_in_thread(step_fn, "failing_step", "pid123")
        assert name == "failing_step"
        assert result is None
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()
        mock_sentry.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 9. _get_doc_text_by_type / _get_all_doc_text / _get_all_doc_texts_by_type
# ═════════════════════════════════════════════════════════════════════════════

class TestDocTextHelpers:
    def test_get_doc_text_by_type_no_docs(self):
        from app.services.analyzer import _get_doc_text_by_type
        db = _make_mock_db()
        assert _get_doc_text_by_type(db, uuid.uuid4(), "CCAP") == ""

    def test_get_doc_text_by_type_with_pages(self):
        from app.services.analyzer import _get_doc_text_by_type
        db = _make_mock_db()
        doc = MagicMock()
        doc.id = uuid.uuid4()
        doc.original_name = "ccap.pdf"
        # First query call: AoDocument filter
        # Second query call: DocumentPage filter
        page = MagicMock()
        page.raw_text = "Page content here"

        call_count = {"n": 0}
        def query_side_effect(model):
            m = MagicMock()
            call_count["n"] += 1
            if call_count["n"] == 1:
                m.filter_by.return_value.all.return_value = [doc]
            else:
                m.filter_by.return_value.order_by.return_value.all.return_value = [page]
            return m

        db.query.side_effect = query_side_effect
        result = _get_doc_text_by_type(db, uuid.uuid4(), "CCAP")
        assert "Page content here" in result

    def test_get_all_doc_texts_by_type_less_than_2(self):
        from app.services.analyzer import _get_all_doc_texts_by_type
        db = _make_mock_db()
        doc = MagicMock()
        doc.doc_type = "RC"
        doc.id = uuid.uuid4()
        page = MagicMock()
        page.raw_text = "Some text"

        call_count = {"n": 0}
        def query_side_effect(model):
            m = MagicMock()
            call_count["n"] += 1
            if call_count["n"] == 1:
                m.filter_by.return_value.all.return_value = [doc]
            else:
                m.filter_by.return_value.order_by.return_value.all.return_value = [page]
            return m

        db.query.side_effect = query_side_effect
        result = _get_all_doc_texts_by_type(db, uuid.uuid4())
        assert "RC" in result


# ═════════════════════════════════════════════════════════════════════════════
# 10. _get_company_profile_dict
# ═════════════════════════════════════════════════════════════════════════════

class TestGetCompanyProfileDict:
    @patch(f"{MOD}._get_project_org_id", return_value=None)
    def test_no_org(self, _):
        from app.services.analyzer import _get_company_profile_dict
        db = _make_mock_db()
        assert _get_company_profile_dict(db, uuid.uuid4()) is None

    @patch(f"{MOD}._get_project_org_id", return_value=uuid.uuid4())
    def test_no_profile(self, _):
        from app.services.analyzer import _get_company_profile_dict
        db = _make_mock_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        assert _get_company_profile_dict(db, uuid.uuid4()) is None

    @patch(f"{MOD}._get_project_org_id", return_value=uuid.uuid4())
    def test_returns_dict(self, _):
        from app.services.analyzer import _get_company_profile_dict
        db = _make_mock_db()
        profile = MagicMock()
        profile.revenue_eur = 5_000_000
        profile.employee_count = 50
        profile.certifications = ["ISO9001"]
        profile.specialties = ["BTP"]
        profile.regions = ["IDF"]
        profile.max_market_size_eur = 2_000_000
        db.query.return_value.filter_by.return_value.first.return_value = profile
        result = _get_company_profile_dict(db, uuid.uuid4())
        assert result["revenue_eur"] == 5_000_000
        assert result["certifications"] == ["ISO9001"]


# ═════════════════════════════════════════════════════════════════════════════
# 11. _report_to_sentry
# ═════════════════════════════════════════════════════════════════════════════

class TestReportToSentry:
    @patch("app.config.settings")
    def test_no_dsn_noop(self, mock_settings):
        """When SENTRY_DSN is empty, no error is raised."""
        from app.services.analyzer import _report_to_sentry
        mock_settings.SENTRY_DSN = ""
        # Should not raise
        _report_to_sentry(RuntimeError("test"), "test_ctx")

    def test_exception_in_sentry_silenced(self):
        """Any exception during Sentry reporting is silently caught."""
        from app.services.analyzer import _report_to_sentry
        # Even if app.config doesn't exist, the bare except catches it
        _report_to_sentry(RuntimeError("test"), "test_ctx")


# ═════════════════════════════════════════════════════════════════════════════
# 12. run_full_analysis — full pipeline with all mocks
# ═════════════════════════════════════════════════════════════════════════════

def _build_full_analysis_patches():
    """Build the comprehensive set of patches needed for run_full_analysis."""
    patches = {}

    # LLM service
    mock_llm = MagicMock()
    mock_llm.reset_usage.return_value = None
    mock_llm.get_model_name.return_value = "claude-test"
    mock_llm.get_usage_summary.return_value = {
        "steps": 5, "total_input": 10000, "total_cached": 2000,
        "estimated_cost_eur": 0.15,
    }
    mock_llm.complete_json.return_value = {
        "project_overview": {"scope": "test", "buyer": "test"},
        "key_points": [], "risks": [], "actions_next_48h": [],
        "checklist": [], "evaluation": {"eligibility_conditions": [], "scoring_criteria": []},
        "score": 75, "recommendation": "GO", "strengths": [], "summary": "OK",
        "breakdown": {"technical_fit": 75, "financial_capacity": 75,
                      "timeline_feasibility": 75, "competitive_position": 75},
        "submission_deadline": None, "execution_start": None,
        "execution_duration_months": None, "site_visit_date": None,
        "questions_deadline": None, "key_dates": [],
        "confidence_overall": 0.85,
    }
    patches["llm"] = mock_llm

    return patches


class TestRunFullAnalysis:
    """Integration-level tests for the full analysis pipeline."""

    def _apply_common_patches(self):
        """Return a list of context managers for common patches."""
        p = _build_full_analysis_patches()
        return [
            patch(f"{MOD}.llm_service", p["llm"]),
            patch(f"{MOD}.retrieve_relevant_chunks", return_value=_fake_chunks()),
            patch(f"{MOD}.format_context", return_value="mocked context text"),
            patch(f"{MOD}.get_max_similarity", return_value=0.85),
            patch(f"{MOD}.detect_project_language", return_value="fr"),
            patch(f"{MOD}.build_summary_prompt", return_value=("sys", "usr")),
            patch(f"{MOD}.build_checklist_prompt", return_value=("sys", "usr")),
            patch(f"{MOD}.build_criteria_prompt", return_value=("sys", "usr")),
            patch(f"{MOD}.build_gonogo_prompt", return_value=("sys", "usr")),
            patch(f"{MOD}.build_deadline_prompt", return_value=("sys", "usr")),
            patch(f"{MOD}.verify_citations_exist", return_value=([], 0)),
            patch(f"{MOD}.compute_overall_confidence", return_value=0.85),
            patch(f"{MOD}.enrich_gonogo_with_profile", side_effect=lambda p, cp, s: p),
            patch(f"{MOD}._get_avg_ocr_quality", return_value=92.0),
            patch(f"{MOD}._save_result"),
            patch(f"{MOD}._save_checklist_items"),
            patch(f"{MOD}._save_criteria_items"),
            patch(f"{MOD}._extract_and_save_deadlines"),
            patch(f"{MOD}._get_doc_text_by_type", return_value=""),
            patch(f"{MOD}._get_all_doc_text", return_value=""),
            patch(f"{MOD}._get_all_doc_texts_by_type", return_value={}),
            patch(f"{MOD}._get_company_profile_dict", return_value=None),
            patch(f"{MOD}._get_project_org_id", return_value=uuid.uuid4()),
            # Make ThreadPoolExecutor run synchronously
            patch(f"{MOD}.ThreadPoolExecutor", _SyncExecutor),
            patch(f"{MOD}.as_completed", _sync_as_completed),
            # SyncSessionLocal for _run_in_thread
            patch(f"{MOD}.SyncSessionLocal", return_value=_make_mock_db()),
        ]

    def test_success_full_pipeline(self):
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            result = run_full_analysis(db, _project_id())
            assert "detected_language" in result
            assert result["detected_language"] == "fr"
            # Batch 1 results should be present
            for key in ("summary", "checklist", "criteria", "gonogo", "timeline"):
                assert key in result, f"Missing {key} in results"
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_english_detection(self):
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        # Override language detection to English
        for i, p in enumerate(patches):
            if hasattr(p, 'attribute') and p.attribute == 'detect_project_language':
                patches[i] = patch(f"{MOD}.detect_project_language", return_value="en")
                break
        else:
            # Find by new_callable hint — just replace at known index
            patches[4] = patch(f"{MOD}.detect_project_language", return_value="en")

        ctx_managers = [p.__enter__() for p in patches]
        try:
            result = run_full_analysis(db, _project_id())
            assert result["detected_language"] == "en"
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_low_ocr_quality_logged(self):
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        # Override OCR quality to be low
        patches[13] = patch(f"{MOD}._get_avg_ocr_quality", return_value=55.0)
        ctx_managers = [p.__enter__() for p in patches]
        try:
            result = run_full_analysis(db, _project_id())
            assert "detected_language" in result
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_batch1_critical_step_failure_raises(self):
        """When a critical batch 1 step (summary) fails, it should raise RuntimeError."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()

        # Make _run_in_thread return None for summary (critical step)
        original_sls = patches[-1]  # SyncSessionLocal
        original_tpe = patches[-2]  # ThreadPoolExecutor

        ctx_managers = [p.__enter__() for p in patches]
        try:
            # Patch _run_in_thread to fail for summary
            with patch(f"{MOD}._run_in_thread") as mock_rit:
                def side_effect(fn, name, pid):
                    if name == "summary":
                        return (name, None)  # critical failure
                    return (name, {"test": "data"})
                mock_rit.side_effect = side_effect

                with pytest.raises(RuntimeError, match="summary"):
                    run_full_analysis(db, _project_id())
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_batch2_noncritical_failure_continues(self):
        """Non-critical batch 2 steps failing should not stop the pipeline."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            # All batch 2 sub-analyzers return empty text → None results
            # Pipeline should complete without raising
            result = run_full_analysis(db, _project_id())
            assert "detected_language" in result
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_batch3_scoring_with_criteria(self):
        """Batch 3 scoring runs when criteria results are present."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            with patch(f"{MOD}.simulate_scoring", create=True,
                       return_value={"note_globale_estimee": 15.5}):
                result = run_full_analysis(db, _project_id())
                assert "detected_language" in result
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_batch3_cashflow_skipped_no_data(self):
        """Cashflow simulation skipped when montant/duree missing."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            result = run_full_analysis(db, _project_id())
            # No ae_analysis or timeline duration → cashflow not in results
            assert "cashflow_simulation" not in result
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_batch3_subcontracting_error_handled(self):
        """Subcontracting error is caught and logged, not raised."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            with patch(f"{MOD}.analyze_subcontracting", create=True,
                       side_effect=RuntimeError("sub error")):
                result = run_full_analysis(db, _project_id())
                assert "subcontracting" not in result
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_verification_step_runs(self):
        """Post-pipeline verification should run."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            with patch(f"{MOD}.verify_cross_analysis_consistency", create=True,
                       return_value={"status": "verified", "issues": [], "score": 95}):
                result = run_full_analysis(db, _project_id())
                assert result.get("verification", {}).get("status") == "verified"
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_llm_usage_persisted(self):
        """LLM usage summary should be saved at end of pipeline."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()
        patches = self._apply_common_patches()
        ctx_managers = [p.__enter__() for p in patches]
        try:
            result = run_full_analysis(db, _project_id())
            # Pipeline completes, db.commit called
            db.commit.assert_called()
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)

    def test_gonogo_llm_error_fallback(self):
        """Go/No-Go should use fallback payload when LLM fails."""
        from app.services.analyzer import run_full_analysis
        db = _make_mock_db()

        call_count = {"n": 0}
        def llm_complete_json_side_effect(*args, **kwargs):
            call_count["n"] += 1
            rk = kwargs.get("required_keys", [])
            if "score" in rk:
                raise RuntimeError("LLM error for gonogo")
            # Return valid payload for other steps
            return {
                "project_overview": {"scope": "test"},
                "key_points": [], "risks": [], "actions_next_48h": [],
                "checklist": [],
                "evaluation": {"eligibility_conditions": [], "scoring_criteria": []},
                "submission_deadline": None, "execution_start": None,
                "execution_duration_months": None, "site_visit_date": None,
                "questions_deadline": None, "key_dates": [],
            }

        p = _build_full_analysis_patches()
        p["llm"].complete_json.side_effect = llm_complete_json_side_effect

        patches = [
            patch(f"{MOD}.llm_service", p["llm"]),
            patch(f"{MOD}.retrieve_relevant_chunks", return_value=_fake_chunks()),
            patch(f"{MOD}.format_context", return_value="ctx"),
            patch(f"{MOD}.get_max_similarity", return_value=0.85),
            patch(f"{MOD}.detect_project_language", return_value="fr"),
            patch(f"{MOD}.build_summary_prompt", return_value=("s", "u")),
            patch(f"{MOD}.build_checklist_prompt", return_value=("s", "u")),
            patch(f"{MOD}.build_criteria_prompt", return_value=("s", "u")),
            patch(f"{MOD}.build_gonogo_prompt", return_value=("s", "u")),
            patch(f"{MOD}.build_deadline_prompt", return_value=("s", "u")),
            patch(f"{MOD}.verify_citations_exist", return_value=([], 0)),
            patch(f"{MOD}.compute_overall_confidence", return_value=0.80),
            patch(f"{MOD}.enrich_gonogo_with_profile", side_effect=lambda p, cp, s: p),
            patch(f"{MOD}._get_avg_ocr_quality", return_value=95.0),
            patch(f"{MOD}._save_result"),
            patch(f"{MOD}._save_checklist_items"),
            patch(f"{MOD}._save_criteria_items"),
            patch(f"{MOD}._extract_and_save_deadlines"),
            patch(f"{MOD}._get_doc_text_by_type", return_value=""),
            patch(f"{MOD}._get_all_doc_text", return_value=""),
            patch(f"{MOD}._get_all_doc_texts_by_type", return_value={}),
            patch(f"{MOD}._get_company_profile_dict", return_value=None),
            patch(f"{MOD}._get_project_org_id", return_value=uuid.uuid4()),
            patch(f"{MOD}.ThreadPoolExecutor", _SyncExecutor),
            patch(f"{MOD}.as_completed", _sync_as_completed),
            patch(f"{MOD}.SyncSessionLocal", return_value=_make_mock_db()),
        ]
        ctx_managers = [pt.__enter__() for pt in patches]
        try:
            result = run_full_analysis(db, _project_id())
            # Go/No-Go should have fallback payload
            gonogo = result.get("gonogo", {})
            assert gonogo.get("score") == 50
            assert gonogo.get("recommendation") == "ATTENTION"
        finally:
            for pt in reversed(patches):
                pt.__exit__(None, None, None)


# ═════════════════════════════════════════════════════════════════════════════
# Synchronous executor helper — makes ThreadPoolExecutor run inline
# ═════════════════════════════════════════════════════════════════════════════

class _SyncFuture:
    """Mimics concurrent.futures.Future for synchronous execution."""
    def __init__(self, fn, *args, **kwargs):
        try:
            self._result = fn(*args, **kwargs)
            self._exception = None
        except Exception as e:
            self._result = None
            self._exception = e

    def result(self, timeout=None):
        if self._exception:
            raise self._exception
        return self._result


class _SyncExecutor:
    """Drop-in replacement for ThreadPoolExecutor that runs synchronously."""
    def __init__(self, max_workers=None):
        self._futures = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def submit(self, fn, *args, **kwargs):
        f = _SyncFuture(fn, *args, **kwargs)
        self._futures.append(f)
        return f


def _sync_as_completed(futures, timeout=None):
    """Drop-in for concurrent.futures.as_completed that works with _SyncFuture."""
    # futures is a dict {future: name} — just yield all keys immediately
    # timeout is accepted but ignored in sync test context
    if isinstance(futures, dict):
        yield from futures.keys()
    else:
        yield from futures


# ═════════════════════════════════════════════════════════════════════════════
# 13. _get_project_org_id
# ═════════════════════════════════════════════════════════════════════════════

class TestGetProjectOrgId:
    def test_project_found(self):
        from app.services.analyzer import _get_project_org_id
        db = _make_mock_db()
        org = uuid.uuid4()
        project = MagicMock()
        project.org_id = org
        db.query.return_value.filter_by.return_value.first.return_value = project
        assert _get_project_org_id(db, uuid.uuid4()) == org

    def test_project_not_found(self):
        from app.services.analyzer import _get_project_org_id
        db = _make_mock_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        assert _get_project_org_id(db, uuid.uuid4()) is None
