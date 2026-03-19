"""Tests pour app/services/prompts.py — prompt builders et templates."""
import pytest

from app.services.prompts import (
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
    _get_system_prompt,
    SUMMARY_SCHEMA,
    CHECKLIST_SCHEMA,
    CRITERIA_SCHEMA,
    GONOGO_SCHEMA,
    SYSTEM_SUMMARY,
    SYSTEM_CHECKLIST,
    SYSTEM_CRITERIA,
    SYSTEM_GONOGO,
    SYSTEM_SUMMARY_EN,
    SYSTEM_CHECKLIST_EN,
    SYSTEM_CRITERIA_EN,
    SYSTEM_GONOGO_EN,
    SYSTEM_CHAT,
    SYSTEM_CHAT_EN,
    SYSTEM_DEADLINE,
    SYSTEM_DEADLINE_EN,
    SYSTEM_WRITING,
    SYSTEM_MEMO_TECHNIQUE,
)


class TestPromptSchemas:
    """Verify JSON schemas are defined and non-empty."""

    def test_summary_schema_non_empty(self):
        assert isinstance(SUMMARY_SCHEMA, str)
        assert len(SUMMARY_SCHEMA) > 50
        assert "project_overview" in SUMMARY_SCHEMA

    def test_checklist_schema_non_empty(self):
        assert isinstance(CHECKLIST_SCHEMA, str)
        assert "checklist" in CHECKLIST_SCHEMA

    def test_criteria_schema_non_empty(self):
        assert isinstance(CRITERIA_SCHEMA, str)
        assert "eligibility_conditions" in CRITERIA_SCHEMA

    def test_gonogo_schema_non_empty(self):
        assert isinstance(GONOGO_SCHEMA, str)
        assert "recommendation" in GONOGO_SCHEMA


class TestSystemPrompts:
    """Verify system prompts contain expected BTP keywords."""

    def test_system_summary_has_btp_keywords(self):
        assert "marchés publics" in SYSTEM_SUMMARY
        assert "BTP" in SYSTEM_SUMMARY
        assert "DCE" in SYSTEM_SUMMARY

    def test_system_checklist_has_keywords(self):
        assert "appels d'offres" in SYSTEM_CHECKLIST
        assert "Éliminatoire" in SYSTEM_CHECKLIST

    def test_system_criteria_has_keywords(self):
        assert "critères d'attribution" in SYSTEM_CRITERIA
        assert "pondérations" in SYSTEM_CRITERIA

    def test_system_gonogo_has_keywords(self):
        assert "Go/No-Go" in SYSTEM_GONOGO
        assert "BTP" in SYSTEM_GONOGO

    def test_system_writing_has_keywords(self):
        assert "appels d'offres" in SYSTEM_WRITING
        assert "professionnel" in SYSTEM_WRITING

    def test_system_memo_technique_has_keywords(self):
        assert "marchés publics" in SYSTEM_MEMO_TECHNIQUE
        assert "BTP" in SYSTEM_MEMO_TECHNIQUE


class TestGetSystemPrompt:
    """Tests for _get_system_prompt() language selection."""

    def test_fr_returns_french_prompt(self):
        result = _get_system_prompt(SYSTEM_SUMMARY, SYSTEM_SUMMARY_EN, "fr")
        assert result is SYSTEM_SUMMARY

    def test_en_returns_english_prompt(self):
        result = _get_system_prompt(SYSTEM_SUMMARY, SYSTEM_SUMMARY_EN, "en")
        assert result is SYSTEM_SUMMARY_EN

    def test_default_returns_french(self):
        result = _get_system_prompt(SYSTEM_SUMMARY, SYSTEM_SUMMARY_EN)
        assert result is SYSTEM_SUMMARY

    def test_unknown_lang_returns_french(self):
        result = _get_system_prompt(SYSTEM_SUMMARY, SYSTEM_SUMMARY_EN, "de")
        assert result is SYSTEM_SUMMARY


class TestBuildSummaryPrompt:
    """Tests for build_summary_prompt()."""

    def test_returns_tuple_of_two_strings(self):
        system, user = build_summary_prompt("Contexte DCE test")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_is_summary_system(self):
        system, _ = build_summary_prompt("Contexte DCE test")
        assert system == SYSTEM_SUMMARY

    def test_user_prompt_contains_context(self):
        _, user = build_summary_prompt("Mon contexte de test")
        assert "Mon contexte de test" in user

    def test_user_prompt_contains_schema(self):
        _, user = build_summary_prompt("Contexte")
        assert "project_overview" in user

    def test_english_lang(self):
        system, _ = build_summary_prompt("Context", lang="en")
        assert system == SYSTEM_SUMMARY_EN


class TestBuildChecklistPrompt:
    """Tests for build_checklist_prompt()."""

    def test_returns_tuple(self):
        result = build_checklist_prompt("contexte")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_contains_context(self):
        _, user = build_checklist_prompt("checklist contexte")
        assert "checklist contexte" in user

    def test_english_version(self):
        system, _ = build_checklist_prompt("context", lang="en")
        assert system == SYSTEM_CHECKLIST_EN


class TestBuildCriteriaPrompt:
    """Tests for build_criteria_prompt()."""

    def test_returns_tuple(self):
        result = build_criteria_prompt("criteres contexte")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_contains_schema(self):
        _, user = build_criteria_prompt("context")
        assert "eligibility_conditions" in user


class TestBuildGonogoPrompt:
    """Tests for build_gonogo_prompt()."""

    def test_returns_tuple(self):
        result = build_gonogo_prompt("contexte dce")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_with_company_profile(self):
        profile = {
            "specialties": ["CVC", "Plomberie"],
            "ca_annuel": "2000000",
            "zones_geo": ["Ile-de-France"],
            "certifications": ["Qualibat"],
        }
        system, user = build_gonogo_prompt("contexte", company_profile=profile)
        assert "CVC" in user
        assert "2000000" in user

    def test_without_company_profile(self):
        _, user = build_gonogo_prompt("contexte")
        assert "Profil de l'entreprise" not in user

    def test_english_version(self):
        system, _ = build_gonogo_prompt("context", lang="en")
        assert system == SYSTEM_GONOGO_EN


class TestBuildWritingPrompt:
    """Tests for build_writing_prompt()."""

    def test_returns_tuple(self):
        result = build_writing_prompt("req", "what", "context")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_contains_all_inputs(self):
        _, user = build_writing_prompt("requirement test", "fournir doc", "contexte dce")
        assert "requirement test" in user
        assert "fournir doc" in user
        assert "contexte dce" in user


class TestBuildDeadlinePrompt:
    """Tests for build_deadline_prompt()."""

    def test_returns_tuple(self):
        result = build_deadline_prompt("dates contexte")
        assert isinstance(result, tuple)

    def test_english_version(self):
        system, _ = build_deadline_prompt("context", lang="en")
        assert system == SYSTEM_DEADLINE_EN


class TestBuildChatPrompt:
    """Tests for build_chat_prompt()."""

    def test_returns_tuple(self):
        result = build_chat_prompt("question?", "context dce")
        assert isinstance(result, tuple)

    def test_contains_question(self):
        _, user = build_chat_prompt("Quel est le budget?", "contexte")
        assert "Quel est le budget?" in user

    def test_english_version(self):
        system, _ = build_chat_prompt("question", "context", lang="en")
        assert system == SYSTEM_CHAT_EN


class TestBuildMemoPrompts:
    """Tests for memo technique prompt builders."""

    def test_memo_intro_returns_tuple(self):
        result = build_memo_intro_prompt(
            project_title="Rénovation Gymnase",
            buyer="Mairie de Lyon",
            scope="CVC complet",
            go_nogo_score=75,
            top_risks=[{"risk": "Pénalités", "severity": "high"}],
            company_profile={"name": "TestCorp", "activity_sector": "BTP"},
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        system, user = result
        assert system == SYSTEM_MEMO_TECHNIQUE
        assert "Rénovation Gymnase" in user
        assert "75" in user

    def test_memo_positioning_returns_tuple(self):
        system, user = build_memo_positioning_prompt(
            company_profile={"name": "TestCorp", "certifications": "Qualibat"},
            gonogo_dimensions={"technical_fit": 80, "financial_capacity": 70},
            eligibility_gaps=["Certification ISO 14001 manquante"],
        )
        assert system == SYSTEM_MEMO_TECHNIQUE
        assert "TestCorp" in user
        assert "80" in user

    def test_memo_action_plan_returns_tuple(self):
        system, user = build_memo_action_plan_prompt(
            actions_48h=[{"action": "Visite site", "priority": "P0", "owner_role": "CT", "deadline_relative": "J+1"}],
            risks=[{"risk": "Pénalités retard", "mitigation": "Anticiper approvisionnements"}],
            deadline_submission="2026-04-15",
        )
        assert system == SYSTEM_MEMO_TECHNIQUE
        assert "Visite site" in user
        assert "2026-04-15" in user

    def test_memo_intro_with_empty_risks(self):
        _, user = build_memo_intro_prompt(
            project_title="Test",
            buyer="Buyer",
            scope="Scope",
            go_nogo_score=50,
            top_risks=[],
            company_profile=None,
        )
        assert "Test" in user

    def test_memo_positioning_with_none_profile(self):
        _, user = build_memo_positioning_prompt(
            company_profile=None,
            gonogo_dimensions=None,
            eligibility_gaps=None,
        )
        assert isinstance(user, str)

    def test_memo_action_plan_with_none_deadline(self):
        _, user = build_memo_action_plan_prompt(
            actions_48h=None,
            risks=None,
            deadline_submission=None,
        )
        assert "Non précisée" in user


class TestAllPromptBuildersCallable:
    """Verify all public prompt builder functions are callable."""

    @pytest.mark.parametrize("func_name", [
        "build_summary_prompt",
        "build_checklist_prompt",
        "build_criteria_prompt",
        "build_gonogo_prompt",
        "build_writing_prompt",
        "build_deadline_prompt",
        "build_chat_prompt",
        "build_memo_intro_prompt",
        "build_memo_positioning_prompt",
        "build_memo_action_plan_prompt",
    ])
    def test_function_is_callable(self, func_name):
        from app.services import prompts
        func = getattr(prompts, func_name)
        assert callable(func)
