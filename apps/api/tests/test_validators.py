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
            category="Administratif",
            requirement="KBIS < 3 mois",
            criticality="Éliminatoire",
            status="MANQUANT",
            citations=[],
            confidence=0.9,
        )
        assert item.criticality == "Éliminatoire"

    def test_unknown_criticality_normalized(self):
        """Unknown criticality should default to Important."""
        item = LLMChecklistItem(
            category="Administratif",
            requirement="Test",
            criticality="invalid_value",
            status="MANQUANT",
            citations=[],
            confidence=0.5,
        )
        # Pydantic validator normalizes unknown criticality to "Important"
        assert item.criticality == "Important"


class TestValidatedGoNoGo:
    def test_score_boundaries(self):
        data = {
            "score": 75,
            "recommendation": "GO",
            "strengths": ["Expérience"],
            "risks": ["Budget serré"],
            "summary": "",
        }
        result = ValidatedGoNoGo.model_validate(data)
        assert 0 <= result.score <= 100
        assert result.recommendation == "GO"


class TestValidatedTimeline:
    def test_timeline_fields(self):
        data = {
            "submission_deadline": "2026-03-15",
            "execution_start": "2026-04-01",
            "execution_duration_months": 12,
            "key_dates": [
                {"label": "Retirer le DCE", "date": "2026-03-15", "mandatory": True},
                {"label": "Visite de site", "date": "2026-03-20", "mandatory": False},
            ],
        }
        result = ValidatedTimeline.model_validate(data)
        assert len(result.key_dates) == 2
        assert result.execution_duration_months == 12
