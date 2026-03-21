"""Tests pour app/services/llm_validators.py — validation Pydantic des sorties LLM.

Couvre les modèles Pydantic, field_validators, model_validators,
coercions, clamping, et fonctions utilitaires (verify_citations_exist,
compute_overall_confidence).
"""
import pytest
from pydantic import ValidationError

from app.services.llm_validators import (
    LLMCitation,
    LLMProjectOverview,
    LLMKeyPoint,
    LLMRisk,
    LLMNextAction,
    ValidatedSummary,
    LLMChecklistItem,
    ValidatedChecklist,
    LLMEligibilityCondition,
    LLMScoringCriterion,
    LLMEvaluation,
    ValidatedCriteria,
    LLMGoNoGoBreakdown,
    ValidatedGoNoGo,
    LLMKeyDate,
    ValidatedTimeline,
    LLMAeClause,
    LLMCcagDerogation,
    ValidatedAeAnalysis,
    ValidatedRcAnalysis,
    LLMConflict,
    verify_citations_exist,
    compute_overall_confidence,
)


# ═══════════════════════════════════════════════════════════════════════════════
# LLMCitation — page coercion
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMCitation:
    def test_int_page(self):
        c = LLMCitation(page=5)
        assert c.page == 5

    def test_float_page(self):
        c = LLMCitation(page=3.7)
        assert c.page == 3

    def test_string_p_dot(self):
        c = LLMCitation(page="p.12")
        assert c.page == 12

    def test_string_page_prefix(self):
        c = LLMCitation(page="Page 42")
        assert c.page == 42

    def test_string_range(self):
        c = LLMCitation(page="p.5-8")
        assert c.page == 5  # prend le premier

    def test_string_no_number(self):
        c = LLMCitation(page="introduction")
        assert c.page == 0

    def test_none_defaults_zero(self):
        c = LLMCitation()
        assert c.page == 0

    def test_empty_string(self):
        c = LLMCitation(page="")
        assert c.page == 0


# ═══════════════════════════════════════════════════════════════════════════════
# LLMProjectOverview — deadline validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMProjectOverview:
    def test_valid_iso_date(self):
        o = LLMProjectOverview(deadline_submission="2026-07-15")
        assert o.deadline_submission == "2026-07-15"

    def test_iso_datetime(self):
        o = LLMProjectOverview(deadline_submission="2026-07-15T12:00:00")
        assert o.deadline_submission == "2026-07-15T12:00:00"

    def test_invalid_date_cleared(self):
        o = LLMProjectOverview(deadline_submission="15 juillet 2026")
        assert o.deadline_submission == ""

    def test_empty_date(self):
        o = LLMProjectOverview(deadline_submission="")
        assert o.deadline_submission == ""

    def test_z_suffix(self):
        o = LLMProjectOverview(deadline_submission="2026-07-15T12:00:00Z")
        assert o.deadline_submission == "2026-07-15T12:00:00Z"


# ═══════════════════════════════════════════════════════════════════════════════
# LLMKeyPoint — ensure_content model validator
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMKeyPoint:
    def test_point_copies_to_value(self):
        kp = LLMKeyPoint(point="Test point", value="")
        assert kp.value == "Test point"

    def test_value_copies_to_point(self):
        kp = LLMKeyPoint(value="Test value", point="")
        assert kp.point == "Test value"

    def test_both_set_unchanged(self):
        kp = LLMKeyPoint(value="A", point="B")
        assert kp.value == "A"
        assert kp.point == "B"


# ═══════════════════════════════════════════════════════════════════════════════
# LLMRisk — severity validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMRisk:
    def test_valid_severity(self):
        r = LLMRisk(risk="Test", severity="high")
        assert r.severity == "high"

    def test_invalid_severity_defaults_medium(self):
        r = LLMRisk(risk="Test", severity="CRITIQUE")
        assert r.severity == "medium"

    def test_case_insensitive(self):
        r = LLMRisk(risk="Test", severity="HIGH")
        assert r.severity == "high"


# ═══════════════════════════════════════════════════════════════════════════════
# LLMNextAction — priority validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMNextAction:
    def test_valid_priorities(self):
        for p in ("P0", "P1", "P2"):
            a = LLMNextAction(action="Test", priority=p)
            assert a.priority == p

    def test_lowercase_normalized(self):
        a = LLMNextAction(action="Test", priority="p0")
        assert a.priority == "P0"

    def test_invalid_defaults_p1(self):
        a = LLMNextAction(action="Test", priority="urgent")
        assert a.priority == "P1"


# ═══════════════════════════════════════════════════════════════════════════════
# ValidatedSummary — confidence clamping
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatedSummary:
    def test_confidence_clamped_high(self):
        s = ValidatedSummary(
            project_overview=LLMProjectOverview(),
            confidence_overall=1.5,
        )
        assert s.confidence_overall == 1.0

    def test_confidence_clamped_low(self):
        s = ValidatedSummary(
            project_overview=LLMProjectOverview(),
            confidence_overall=-0.5,
        )
        assert s.confidence_overall == 0.0

    def test_confidence_none(self):
        s = ValidatedSummary(
            project_overview=LLMProjectOverview(),
            confidence_overall=None,
        )
        assert s.confidence_overall is None

    def test_full_summary(self):
        s = ValidatedSummary(
            project_overview={"title": "Test", "buyer": "Ville de Paris"},
            key_points=[{"point": "Point A", "importance": "high"}],
            risks=[{"risk": "Risque 1", "severity": "high"}],
            actions_next_48h=[{"action": "Act 1", "priority": "P0"}],
            confidence_overall=0.85,
        )
        assert len(s.key_points) == 1
        assert len(s.risks) == 1
        assert s.actions_next_48h[0].priority == "P0"


# ═══════════════════════════════════════════════════════════════════════════════
# LLMChecklistItem — category, criticality, status, confidence validators
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMChecklistItem:
    def test_valid_category(self):
        item = LLMChecklistItem(requirement="Test", category="Technique")
        assert item.category == "Technique"

    def test_fuzzy_category_match(self):
        item = LLMChecklistItem(requirement="Test", category="technique_advanced")
        assert item.category == "Technique"

    def test_unknown_category_defaults_admin(self):
        item = LLMChecklistItem(requirement="Test", category="Unknown")
        assert item.category == "Administratif"

    def test_criticality_mapping(self):
        item = LLMChecklistItem(requirement="Test", criticality="eliminatoire")
        assert item.criticality == "Éliminatoire"

    def test_criticality_info(self):
        item = LLMChecklistItem(requirement="Test", criticality="information")
        assert item.criticality == "Info"

    def test_unknown_criticality_defaults_important(self):
        item = LLMChecklistItem(requirement="Test", criticality="critical")
        assert item.criticality == "Important"

    def test_status_mapping(self):
        item = LLMChecklistItem(requirement="Test", status="ok")
        assert item.status == "OK"

    def test_status_a_clarifier(self):
        item = LLMChecklistItem(requirement="Test", status="a clarifier")
        assert item.status == "À CLARIFIER"

    def test_unknown_status_defaults_manquant(self):
        item = LLMChecklistItem(requirement="Test", status="pending")
        assert item.status == "MANQUANT"

    def test_confidence_clamped(self):
        item = LLMChecklistItem(requirement="Test", confidence=1.5)
        assert item.confidence == 1.0

    def test_confidence_clamped_low(self):
        item = LLMChecklistItem(requirement="Test", confidence=-0.3)
        assert item.confidence == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# LLMScoringCriterion — weight validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMScoringCriterion:
    def test_valid_weight(self):
        c = LLMScoringCriterion(criterion="Prix", weight_percent=40.0)
        assert c.weight_percent == 40.0

    def test_out_of_range_weight_none(self):
        c = LLMScoringCriterion(criterion="Prix", weight_percent=150.0)
        assert c.weight_percent is None

    def test_negative_weight_none(self):
        c = LLMScoringCriterion(criterion="Prix", weight_percent=-5.0)
        assert c.weight_percent is None


# ═══════════════════════════════════════════════════════════════════════════════
# LLMEvaluation — total_weight_check coercion
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMEvaluation:
    def test_total_weight_from_int(self):
        e = LLMEvaluation(total_weight_check=100)
        assert e.total_weight_check == 100.0

    def test_total_weight_from_string(self):
        e = LLMEvaluation(total_weight_check="95,5%")
        assert e.total_weight_check == 95.5

    def test_total_weight_from_dict(self):
        e = LLMEvaluation(total_weight_check={"total": 100})
        assert e.total_weight_check == 100.0

    def test_total_weight_from_bad_string(self):
        e = LLMEvaluation(total_weight_check="not a number")
        assert e.total_weight_check is None

    def test_total_weight_none(self):
        e = LLMEvaluation(total_weight_check=None)
        assert e.total_weight_check is None


# ═══════════════════════════════════════════════════════════════════════════════
# ValidatedGoNoGo — score/recommendation coherence
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatedGoNoGo:
    def test_score_clamped(self):
        g = ValidatedGoNoGo(score=150)
        assert g.score == 100

    def test_negative_score_clamped(self):
        g = ValidatedGoNoGo(score=-10)
        assert g.score == 0

    def test_recommendation_go(self):
        g = ValidatedGoNoGo(score=80, recommendation="GO")
        assert g.recommendation == "GO"

    def test_recommendation_fuzzy_go(self):
        g = ValidatedGoNoGo(score=80, recommendation="go for it")
        assert g.recommendation == "GO"

    def test_recommendation_fuzzy_nogo(self):
        g = ValidatedGoNoGo(score=20, recommendation="no-go too risky")
        assert g.recommendation == "NO-GO"

    def test_incoherence_high_score_nogo_corrected(self):
        g = ValidatedGoNoGo(score=85, recommendation="NO-GO")
        assert g.recommendation == "GO"

    def test_incoherence_low_score_go_corrected(self):
        g = ValidatedGoNoGo(score=30, recommendation="GO")
        assert g.recommendation == "NO-GO"

    def test_breakdown_scores_clamped(self):
        b = LLMGoNoGoBreakdown(technical_fit=150, financial_capacity=-10)
        assert b.technical_fit == 100
        assert b.financial_capacity == 0


# ═══════════════════════════════════════════════════════════════════════════════
# ValidatedTimeline — date validation, duration
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatedTimeline:
    def test_valid_dates(self):
        t = ValidatedTimeline(
            submission_deadline="2026-07-15",
            execution_start="2026-09-01",
        )
        assert t.submission_deadline == "2026-07-15"

    def test_invalid_date_cleared(self):
        t = ValidatedTimeline(submission_deadline="July 2026")
        assert t.submission_deadline is None

    def test_duration_valid(self):
        t = ValidatedTimeline(execution_duration_months=12)
        assert t.execution_duration_months == 12

    def test_duration_too_long_cleared(self):
        t = ValidatedTimeline(execution_duration_months=300)
        assert t.execution_duration_months is None

    def test_key_date_valid(self):
        d = LLMKeyDate(label="Visite site", date="2026-06-15", mandatory=True)
        assert d.date == "2026-06-15"
        assert d.mandatory is True

    def test_key_date_invalid_cleared(self):
        d = LLMKeyDate(label="Test", date="invalid")
        assert d.date is None


# ═══════════════════════════════════════════════════════════════════════════════
# AE Analysis — risk level, impact validators
# ═══════════════════════════════════════════════════════════════════════════════


class TestLLMAeClause:
    def test_valid_risk_levels(self):
        for rl in ("CRITIQUE", "HAUT", "MOYEN", "BAS"):
            c = LLMAeClause(clause_type="test", description="d", risk_level=rl)
            assert c.risk_level == rl

    def test_invalid_risk_defaults_moyen(self):
        c = LLMAeClause(clause_type="test", description="d", risk_level="unknown")
        assert c.risk_level == "MOYEN"


class TestLLMCcagDerogation:
    def test_impact_defavorable(self):
        d = LLMCcagDerogation(impact="DEFAVORABLE")
        assert d.impact == "DEFAVORABLE"

    def test_impact_fuzzy_negative(self):
        d = LLMCcagDerogation(impact="négatif pour l'entreprise")
        assert d.impact == "DEFAVORABLE"

    def test_impact_fuzzy_positive(self):
        d = LLMCcagDerogation(impact="favorable")
        assert d.impact == "FAVORABLE"

    def test_impact_unknown_defaults_neutre(self):
        d = LLMCcagDerogation(impact="unknown")
        assert d.impact == "NEUTRE"


class TestValidatedAeAnalysis:
    def test_score_clamped(self):
        a = ValidatedAeAnalysis(score_risque_global=150)
        assert a.score_risque_global == 100

    def test_score_negative_clamped(self):
        a = ValidatedAeAnalysis(score_risque_global=-5)
        assert a.score_risque_global == 0


# ═══════════════════════════════════════════════════════════════════════════════
# verify_citations_exist & compute_overall_confidence
# ═══════════════════════════════════════════════════════════════════════════════


class TestVerifyCitationsExist:
    """verify_citations_exist(items: list[dict], chunks: list[dict]) -> (items, nb_verified)"""

    def test_empty_items_and_chunks(self):
        items, nb = verify_citations_exist([], [])
        assert nb == 0

    def test_with_matching_citation(self):
        items = [
            {"citations": [{"doc": "CCAP", "page": 5, "quote": "les pénalités de retard sont fixées par article"}]}
        ]
        chunks = [{"content": "Les pénalités de retard sont fixées par article 14.1 du CCAP."}]
        result_items, nb = verify_citations_exist(items, chunks)
        assert nb >= 1
        assert result_items[0]["citations"][0]["verified"] is True

    def test_with_no_match(self):
        items = [
            {"citations": [{"doc": "RC", "page": 1, "quote": "cette phrase n'existe absolument pas dans le texte source"}]}
        ]
        chunks = [{"content": "Un contenu totalement différent sans rapport."}]
        _, nb = verify_citations_exist(items, chunks)
        assert nb == 0

    def test_short_quote_not_verified(self):
        items = [{"citations": [{"doc": "RC", "page": 1, "quote": "court"}]}]
        chunks = [{"content": "court"}]
        _, nb = verify_citations_exist(items, chunks)
        assert nb == 0  # quote < 10 chars → not verified

    def test_no_chunks(self):
        items = [{"citations": [{"doc": "RC", "page": 1, "quote": "une citation suffisamment longue pour vérification"}]}]
        _, nb = verify_citations_exist(items, [])
        assert nb == 0


class TestComputeOverallConfidence:
    """compute_overall_confidence(payload: dict, chunks: list[dict], ...) -> float"""

    def test_empty_payload_and_chunks(self):
        result = compute_overall_confidence({}, [])
        assert isinstance(result, float)

    def test_with_good_chunks(self):
        chunks = [
            {"content": "test", "similarity": 0.8},
            {"content": "test2", "similarity": 0.6},
        ]
        payload = {"key": "value", "other": "data"}
        result = compute_overall_confidence(payload, chunks)
        assert 0.0 <= result <= 1.0

    def test_with_ocr_quality(self):
        result = compute_overall_confidence(
            {"key": "value"},
            [{"content": "c", "similarity": 0.9}],
            ocr_quality=95.0,
        )
        assert 0.0 <= result <= 1.0

    def test_low_ocr_reduces_confidence(self):
        high = compute_overall_confidence(
            {"key": "value"},
            [{"content": "c", "similarity": 0.9}],
            ocr_quality=95.0,
        )
        low = compute_overall_confidence(
            {"key": "value"},
            [{"content": "c", "similarity": 0.9}],
            ocr_quality=40.0,
        )
        assert low <= high


# ═══════════════════════════════════════════════════════════════════════════════
# ValidatedCriteria — weights sum check
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatedCriteria:
    def test_valid_weights_100(self):
        c = ValidatedCriteria(evaluation={
            "scoring_criteria": [
                {"criterion": "Prix", "weight_percent": 50},
                {"criterion": "Technique", "weight_percent": 50},
            ]
        })
        assert c.evaluation.total_weight_check is None  # pas de warning si =100

    def test_weights_far_from_100_logged(self):
        c = ValidatedCriteria(evaluation={
            "scoring_criteria": [
                {"criterion": "Prix", "weight_percent": 20},
                {"criterion": "Technique", "weight_percent": 30},
            ]
        })
        # total = 50, devrait être logué et total_weight_check mis à jour
        assert c.evaluation.total_weight_check == 50.0

    def test_eligibility_type_validation(self):
        ec = LLMEligibilityCondition(condition="Test", type="invalid")
        assert ec.type == "hard"

    def test_eligibility_soft_type(self):
        ec = LLMEligibilityCondition(condition="Test", type="soft")
        assert ec.type == "soft"


# ═══════════════════════════════════════════════════════════════════════════════
# RC Analysis
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatedRcAnalysis:
    def test_defaults(self):
        rc = ValidatedRcAnalysis()
        assert rc.variantes_autorisees is False
        assert rc.langue_offre == "français"
        assert rc.devise_offre == "EUR"
        assert rc.confidence_overall == 0.5

    def test_full_construction(self):
        rc = ValidatedRcAnalysis(
            visite_site_obligatoire=True,
            variantes_autorisees=True,
            nombre_lots=3,
            procedure_type="ouvert",
        )
        assert rc.visite_site_obligatoire is True
        assert rc.nombre_lots == 3
