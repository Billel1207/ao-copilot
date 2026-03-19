"""Tests for app.services.verification — cross-analysis consistency checks."""
import pytest

from app.services.verification import verify_cross_analysis_consistency


# ---------------------------------------------------------------------------
# No issues — clean verification
# ---------------------------------------------------------------------------

class TestVerifiedStatus:
    def test_empty_results(self):
        result = verify_cross_analysis_consistency("proj-1", {})
        assert result["status"] == "verified"
        assert result["score"] == 100
        assert result["issues"] == []
        assert result["checks_performed"] == 6

    def test_all_consistent(self):
        results = {
            "summary": {
                "project_overview": {"deadline_submission": "2026-04-01"},
            },
            "timeline": {"submission_deadline": "2026-04-01"},
            "gonogo": {"score": 75, "recommendation": "GO", "breakdown": {}},
            "criteria": {"evaluation": {"scoring_criteria": [
                {"criterion": "Prix", "weight_percent": 60},
                {"criterion": "Technique", "weight_percent": 40},
            ]}},
            "ccap": {"score_risque_global": 50, "clauses_risquees": []},
            "conflicts": {"conflicts": []},
            "checklist": {"checklist": [
                {"criticality": "Éliminatoire", "requirement": "DC1"},
                {"criticality": "Important", "requirement": "DC2"},
            ]},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        assert result["status"] == "verified"
        assert result["score"] == 100


# ---------------------------------------------------------------------------
# Date mismatch (summary vs timeline)
# ---------------------------------------------------------------------------

class TestDateMismatch:
    def test_date_mismatch_detected(self):
        results = {
            "summary": {"project_overview": {"deadline_submission": "2026-04-01"}},
            "timeline": {"submission_deadline": "2026-05-15"},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        issues = result["issues"]
        assert len(issues) == 1
        assert issues[0]["type"] == "date_mismatch"
        assert issues[0]["severity"] == "high"
        assert result["status"] == "inconsistencies_found"

    def test_no_mismatch_when_dates_match(self):
        results = {
            "summary": {"project_overview": {"deadline_submission": "2026-04-01"}},
            "timeline": {"submission_deadline": "2026-04-01"},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        date_issues = [i for i in result["issues"] if i["type"] == "date_mismatch"]
        assert len(date_issues) == 0

    def test_no_mismatch_when_one_missing(self):
        results = {
            "summary": {"project_overview": {"deadline_submission": ""}},
            "timeline": {"submission_deadline": "2026-04-01"},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        date_issues = [i for i in result["issues"] if i["type"] == "date_mismatch"]
        assert len(date_issues) == 0


# ---------------------------------------------------------------------------
# Go/No-Go score vs breakdown
# ---------------------------------------------------------------------------

class TestGoNoGoConsistency:
    def test_score_mismatch_detected(self):
        results = {
            "gonogo": {
                "score": 90,
                "recommendation": "GO",
                "breakdown": {
                    "technical": 30,
                    "financial": 25,
                    "timeline": 20,
                    "competitive": 15,
                },
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        score_issues = [i for i in result["issues"] if i["type"] == "score_mismatch"]
        # Weighted avg = 30*0.30 + 25*0.20 + 20*0.25 + 15*0.25 = 9+5+5+3.75 = 22.75
        # |90 - 22.75| = 67.25 > 15, so should flag
        assert len(score_issues) == 1

    def test_recommendation_go_with_low_score(self):
        results = {
            "gonogo": {
                "score": 30,
                "recommendation": "GO",
                "breakdown": {},
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        rec_issues = [i for i in result["issues"] if i["type"] == "recommendation_mismatch"]
        assert len(rec_issues) == 1
        assert "GO" in rec_issues[0]["message"]

    def test_recommendation_nogo_with_high_score(self):
        results = {
            "gonogo": {
                "score": 60,
                "recommendation": "NO-GO",
                "breakdown": {},
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        rec_issues = [i for i in result["issues"] if i["type"] == "recommendation_mismatch"]
        assert len(rec_issues) == 1

    def test_consistent_recommendation(self):
        results = {
            "gonogo": {
                "score": 80,
                "recommendation": "GO",
                "breakdown": {},
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        rec_issues = [i for i in result["issues"] if i["type"] == "recommendation_mismatch"]
        assert len(rec_issues) == 0


# ---------------------------------------------------------------------------
# Criteria weight sum
# ---------------------------------------------------------------------------

class TestCriteriaWeightSum:
    def test_weights_dont_sum_to_100(self):
        results = {
            "criteria": {
                "evaluation": {
                    "scoring_criteria": [
                        {"criterion": "Prix", "weight_percent": 30},
                        {"criterion": "Technique", "weight_percent": 30},
                    ],
                },
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        weight_issues = [i for i in result["issues"] if i["type"] == "weight_sum_error"]
        assert len(weight_issues) == 1
        assert "60%" in weight_issues[0]["message"]

    def test_weights_sum_close_to_100(self):
        results = {
            "criteria": {
                "evaluation": {
                    "scoring_criteria": [
                        {"criterion": "Prix", "weight_percent": 60},
                        {"criterion": "Technique", "weight_percent": 38},
                    ],
                },
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        weight_issues = [i for i in result["issues"] if i["type"] == "weight_sum_error"]
        assert len(weight_issues) == 0  # 98 is within tolerance of 5


# ---------------------------------------------------------------------------
# CCAP risk score vs risky clauses
# ---------------------------------------------------------------------------

class TestCcapRiskConsistency:
    def test_low_score_many_high_risk_clauses(self):
        results = {
            "ccap": {
                "score_risque_global": 20,
                "clauses_risquees": [
                    {"clause": "C1", "risque": "élevé"},
                    {"clause": "C2", "risque": "élevé"},
                    {"clause": "C3", "risque": "élevé"},
                ],
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        risk_issues = [i for i in result["issues"] if i["type"] == "risk_score_mismatch"]
        assert len(risk_issues) == 1

    def test_high_score_few_risk_clauses(self):
        results = {
            "ccap": {
                "score_risque_global": 60,
                "clauses_risquees": [
                    {"clause": "C1", "risque": "élevé"},
                ],
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        risk_issues = [i for i in result["issues"] if i["type"] == "risk_score_mismatch"]
        assert len(risk_issues) == 0


# ---------------------------------------------------------------------------
# Conflicts vs Go/No-Go
# ---------------------------------------------------------------------------

class TestConflictConsistency:
    def test_many_high_conflicts_with_go(self):
        results = {
            "conflicts": {
                "conflicts": [
                    {"severity": "high", "desc": "c1"},
                    {"severity": "high", "desc": "c2"},
                    {"severity": "high", "desc": "c3"},
                ],
            },
            "gonogo": {"score": 85, "recommendation": "GO"},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        issues = [i for i in result["issues"] if i["type"] == "conflict_score_mismatch"]
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# Checklist completeness
# ---------------------------------------------------------------------------

class TestChecklistCompleteness:
    def test_no_eliminatory_items_flagged(self):
        results = {
            "checklist": {
                "checklist": [
                    {"criticality": "Important", "requirement": f"R{i}"} for i in range(10)
                ],
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        issues = [i for i in result["issues"] if i["type"] == "checklist_incomplete"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "low"

    def test_has_eliminatory_items(self):
        results = {
            "checklist": {
                "checklist": [
                    {"criticality": "Éliminatoire", "requirement": "DC1"},
                    {"criticality": "Important", "requirement": "DC2"},
                ] + [{"criticality": "Important", "requirement": f"R{i}"} for i in range(5)],
            },
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        issues = [i for i in result["issues"] if i["type"] == "checklist_incomplete"]
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Consistency score calculation
# ---------------------------------------------------------------------------

class TestConsistencyScore:
    def test_high_severity_lowers_score(self):
        results = {
            "summary": {"project_overview": {"deadline_submission": "2026-04-01"}},
            "timeline": {"submission_deadline": "2026-05-01"},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        assert result["score"] == 85  # 100 - 15 (one high severity)

    def test_multiple_issues_compound(self):
        results = {
            "summary": {"project_overview": {"deadline_submission": "2026-04-01"}},
            "timeline": {"submission_deadline": "2026-05-01"},
            "gonogo": {"score": 30, "recommendation": "GO", "breakdown": {}},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        # date_mismatch (high=15) + recommendation_mismatch (high=15) = 30
        assert result["score"] == 70

    def test_score_never_negative(self):
        """Score should be clamped to 0-100."""
        results = {
            "summary": {"project_overview": {"deadline_submission": "2026-04-01"}},
            "timeline": {"submission_deadline": "2026-05-01"},
            "gonogo": {"score": 30, "recommendation": "GO", "breakdown": {
                "technical": 10, "financial": 10, "timeline": 10, "competitive": 10,
            }},
            "criteria": {"evaluation": {"scoring_criteria": [
                {"criterion": "A", "weight_percent": 10},
            ]}},
            "ccap": {"score_risque_global": 10, "clauses_risquees": [
                {"risque": "élevé"}, {"risque": "élevé"}, {"risque": "élevé"},
            ]},
            "conflicts": {"conflicts": [
                {"severity": "high"}, {"severity": "high"}, {"severity": "high"},
            ]},
            "checklist": {"checklist": [
                {"criticality": "Important", "requirement": f"R{i}"} for i in range(10)
            ]},
        }
        result = verify_cross_analysis_consistency("proj-1", results)
        assert result["score"] >= 0
        assert result["score"] <= 100
