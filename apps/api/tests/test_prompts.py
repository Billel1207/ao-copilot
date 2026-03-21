"""Tests for app.services.prompts - prompt builders and schemas."""
import pytest

from app.services.prompts import (
    _get_system_prompt,
    build_summary_prompt,
    build_checklist_prompt,
    build_criteria_prompt,
    build_gonogo_prompt,
    build_writing_prompt,
    build_deadline_prompt,
    build_chat_prompt,
    build_memo_intro_prompt,
    build_memo_positioning_prompt,
    build_memo_action_plan_prompt,
    SYSTEM_SUMMARY,
    SYSTEM_SUMMARY_EN,
    SYSTEM_CHECKLIST,
    SYSTEM_CHECKLIST_EN,
    SYSTEM_CRITERIA,
    SYSTEM_CRITERIA_EN,
    SYSTEM_GONOGO,
    SYSTEM_GONOGO_EN,
    SYSTEM_DEADLINE,
    SYSTEM_DEADLINE_EN,
    SYSTEM_CHAT,
    SYSTEM_CHAT_EN,
    SYSTEM_WRITING,
    SYSTEM_MEMO_TECHNIQUE,
)

class TestGetSystemPrompt:
    def test_fr_returns_french(self):
        result = _get_system_prompt("FR", "EN", "fr")
        assert result == "FR"

    def test_en_returns_english(self):
        result = _get_system_prompt("FR", "EN", "en")
        assert result == "EN"

    def test_default_is_french(self):
        result = _get_system_prompt("FR", "EN")
        assert result == "FR"

    def test_unknown_lang_returns_french(self):
        result = _get_system_prompt("FR", "EN", "de")
        assert result == "FR"


class TestBuildSummaryPrompt:
    def test_returns_tuple(self):
        s, u = build_summary_prompt("context text")
        assert isinstance(s, str)
        assert isinstance(u, str)

    def test_french_system_prompt(self):
        s, _ = build_summary_prompt("ctx", lang="fr")
        assert s == SYSTEM_SUMMARY

    def test_english_system_prompt(self):
        s, _ = build_summary_prompt("ctx", lang="en")
        assert s == SYSTEM_SUMMARY_EN

    def test_context_in_user_prompt(self):
        _, u = build_summary_prompt("my DCE context")
        assert "my DCE context" in u

    def test_schema_in_user_prompt(self):
        _, u = build_summary_prompt("ctx")
        assert "project_overview" in u


class TestBuildChecklistPrompt:
    def test_french_default(self):
        s, _ = build_checklist_prompt("ctx")
        assert s == SYSTEM_CHECKLIST

    def test_english(self):
        s, _ = build_checklist_prompt("ctx", lang="en")
        assert s == SYSTEM_CHECKLIST_EN

    def test_schema_present(self):
        _, u = build_checklist_prompt("ctx")
        assert "checklist" in u


class TestBuildCriteriaPrompt:
    def test_french(self):
        s, _ = build_criteria_prompt("ctx")
        assert s == SYSTEM_CRITERIA

    def test_english(self):
        s, _ = build_criteria_prompt("ctx", lang="en")
        assert s == SYSTEM_CRITERIA_EN

    def test_context_embedded(self):
        _, u = build_criteria_prompt("special context")
        assert "special context" in u


class TestBuildGonogoPrompt:
    def test_basic(self):
        s, u = build_gonogo_prompt("dce context")
        assert s == SYSTEM_GONOGO
        assert "dce context" in u

    def test_english(self):
        s, _ = build_gonogo_prompt("ctx", lang="en")
        assert s == SYSTEM_GONOGO_EN

    def test_with_company_profile(self):
        profile = {"specialties": ["CVC", "Plomberie"], "ca_annuel": "2M", "zones_geo": ["IDF"], "certifications": ["Qualibat"]}
        s, u = build_gonogo_prompt("ctx", company_profile=profile)
        assert "CVC" in u
        assert "2M" in u
        assert "Qualibat" in u

    def test_without_company_profile(self):
        _, u = build_gonogo_prompt("ctx", company_profile=None)
        assert "Profil" not in u

    def test_company_profile_empty_dict(self):
        _, u = build_gonogo_prompt("ctx", company_profile={})
        # Empty dict should still produce a valid prompt (no crash)
        assert "score" in u

    def test_schema_in_user(self):
        _, u = build_gonogo_prompt("ctx")
        assert "score" in u
        assert "recommendation" in u


class TestBuildWritingPrompt:
    def test_basic(self):
        s, u = build_writing_prompt("req", "provide", "ctx")
        assert s == SYSTEM_WRITING
        assert "req" in u
        assert "provide" in u

    def test_schema_present(self):
        _, u = build_writing_prompt("r", "p", "c")
        assert "generated_text" in u


class TestBuildDeadlinePrompt:
    def test_french(self):
        s, _ = build_deadline_prompt("ctx")
        assert s == SYSTEM_DEADLINE

    def test_english(self):
        s, _ = build_deadline_prompt("ctx", lang="en")
        assert s == SYSTEM_DEADLINE_EN

    def test_schema_present(self):
        _, u = build_deadline_prompt("ctx")
        assert "submission_deadline" in u


class TestBuildChatPrompt:
    def test_french(self):
        s, u = build_chat_prompt("What?", "context")
        assert s == SYSTEM_CHAT
        assert "What?" in u

    def test_english(self):
        s, _ = build_chat_prompt("q", "ctx", lang="en")
        assert s == SYSTEM_CHAT_EN


class TestBuildMemoIntroPrompt:
    def test_basic(self):
        risks = [{"risk": "Penalites", "severity": "high"}]
        profile = {"name": "BTP Corp", "activity_sector": "Constr", "annual_revenue_eur": 5000000, "certifications": ["Q"], "regions": ["IDF"]}
        s, u = build_memo_intro_prompt("Renovation", "Mairie", "CVC", 75, risks, profile)
        assert s == SYSTEM_MEMO_TECHNIQUE
        assert "Renovation" in u
        assert "75/100" in u
        assert "Penalites" in u
        assert "BTP Corp" in u

    def test_empty_risks(self):
        s, _ = build_memo_intro_prompt("T", "B", "S", 50, [], {})
        assert s == SYSTEM_MEMO_TECHNIQUE

    def test_none_profile(self):
        s, _ = build_memo_intro_prompt("T", "B", "S", 50, [], None)
        assert s == SYSTEM_MEMO_TECHNIQUE

    def test_risks_capped_at_3(self):
        risks = [{"risk": "R" + str(i), "severity": "low"} for i in range(10)]
        _, u = build_memo_intro_prompt("T", "B", "S", 50, risks, {})
        assert "R0" in u
        assert "R2" in u
        assert "R3" not in u

    def test_risks_alternative_keys(self):
        risks = [{"titre": "Risque Alt", "niveau": "high"}]
        _, u = build_memo_intro_prompt("T", "B", "S", 50, risks, {})
        assert "Risque Alt" in u