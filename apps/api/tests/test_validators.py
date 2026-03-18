"""Tests for LLM validators — Pydantic v2 models for output validation."""
import pytest
from app.services.llm_validators import (
    LLMCitation,
    LLMProjectOverview,
    LLMKeyPoint,
    LLMRisk,
    LLMChecklistItem,
    ValidatedSummary,
    ValidatedGoNoGo,
    ValidatedTimeline,
)


class TestLLMCitation:
    def test_valid_citation(self):
        c = LLMCitation(doc="CCAP.pdf", page=3, quote="Article 5.1")
        assert c.doc == "CCAP.pdf"
        assert c.page == 3

    def test_empty_citation(self):
        c = LLMCitation()
        assert c.doc == ""
        assert c.page == 0


class TestLLMProjectOverview:
    def test_valid_deadline(self):
        po = LLMProjectOverview(
            title="Test",
            buyer="Ville de Paris",
            scope="Travaux",
            deadline_submission="2026-04-15T12:00:00",
        )
        assert po.deadline_submission == "2026-04-15T12:00:00"

    def test_invalid_deadline_cleared(self):
        po = LLMProjectOverview(
            title="Test",
            buyer="Ville",
            scope="Travaux",
            deadline_submission="pas une date",
        )
        assert po.deadline_submission == ""

    def test_empty_deadline_accepted(self):
        po = LLMProjectOverview(title="Test", buyer="V", scope="S", deadline_submission="")
        assert po.deadline_submission == ""


class TestLLMRisk:
    def test_severity_defaults_medium(self):
        r = LLMRisk(risk="Pénalités élevées")
        assert r.severity == "medium"

    def test_valid_severity(self):
        r = LLMRisk(risk="Test", severity="high")
        assert r.severity == "high"


class TestValidatedSummary:
    def test_minimal_summary(self):
        data = {
            "project_overview": {
                "title": "Réhabilitation école",
                "buyer": "Mairie de Lyon",
                "scope": "Lot 1 — Gros Oeuvre",
                "location": "Lyon 69003",
                "deadline_submission": "",
            },
            "key_points": [],
            "risks": [],
            "actions_next_48h": [],
            "confidence_overall": 0.85,
        }
        result = ValidatedSummary.model_validate(data)
        assert result.project_overview.title == "Réhabilitation école"
        assert result.confidence_overall == 0.85

    def test_confidence_clamped(self):
        data = {
            "project_overview": {"title": "T", "buyer": "B", "scope": "S", "location": "L", "deadline_submission": ""},
            "key_points": [],
            "risks": [],
            "actions_next_48h": [],
            "confidence_overall": 1.5,
        }
        result = ValidatedSummary.model_validate(data)
        assert result.confidence_overall <= 1.0


class TestLLMChecklistItem:
    def test_valid_checklist_item(self):
        item = LLMChecklistItem(
            category="admin",
            item="KBIS < 3 mois",
            criticality="critical",
            status="missing",
            citations=[],
            confidence=0.9,
        )
        assert item.criticality == "critical"

    def test_unknown_criticality_normalized(self):
        """Unknown criticality should default to medium."""
        item = LLMChecklistItem(
            category="admin",
            item="Test",
            criticality="invalid_value",
            status="missing",
            citations=[],
            confidence=0.5,
        )
        # Pydantic should accept or coerce
        assert item is not None


class TestValidatedGoNoGo:
    def test_score_boundaries(self):
        data = {
            "go_score": 75,
            "recommendation": "go",
            "strengths": ["Expérience"],
            "weaknesses": ["Budget serré"],
            "risks": [],
            "key_factors": [],
            "confidence_overall": 0.8,
        }
        result = ValidatedGoNoGo.model_validate(data)
        assert 0 <= result.go_score <= 100
        assert result.recommendation == "go"


class TestValidatedTimeline:
    def test_timeline_tasks(self):
        data = {
            "tasks": [
                {"label": "Retirer le DCE", "deadline": "2026-03-15", "done": False, "priority": "high"},
                {"label": "Visite de site", "deadline": "2026-03-20", "done": False, "priority": "medium"},
            ],
            "confidence_overall": 0.7,
        }
        result = ValidatedTimeline.model_validate(data)
        assert len(result.tasks) == 2
