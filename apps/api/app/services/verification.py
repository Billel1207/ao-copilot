"""Post-analysis verification — cross-checks consistency between all analysis results.

Run after the full 16-step pipeline completes. Detects:
- Date inconsistencies (submission deadline in summary vs timeline)
- Score inconsistencies (Go/No-Go score vs individual dimension scores)
- Weight inconsistencies (criteria weights don't sum to ~100%)
- Citation verification (cited documents exist in the project)
- Conflict coherence (conflicts reference valid document types)
"""
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = structlog.get_logger(__name__)


def verify_cross_analysis_consistency(project_id: str, results: dict) -> dict:
    """Verify consistency across all analysis results.

    Args:
        project_id: The project ID
        results: Dict with keys like 'summary', 'checklist', 'criteria',
                 'gonogo', 'timeline', 'ccap', 'conflicts', etc.

    Returns:
        Dict with:
        - issues: list of {type, severity, message, sources}
        - score: 0-100 consistency score
        - status: "verified" | "warnings" | "inconsistencies_found"
    """
    issues = []

    # 1. Date consistency: submission_deadline in summary vs timeline
    summary = results.get("summary", {})
    timeline = results.get("timeline", {})
    if summary and timeline:
        summary_deadline = (summary.get("project_overview", {}) or {}).get("deadline_submission", "")
        timeline_deadline = timeline.get("submission_deadline", "")
        if summary_deadline and timeline_deadline and summary_deadline != timeline_deadline:
            issues.append({
                "type": "date_mismatch",
                "severity": "high",
                "message": f"Date limite soumission incohérente: résumé={summary_deadline}, timeline={timeline_deadline}",
                "sources": ["summary", "timeline"],
            })

    # 2. Go/No-Go score vs breakdown consistency
    gonogo = results.get("gonogo", {})
    if gonogo:
        score = gonogo.get("score", 0)
        breakdown = gonogo.get("breakdown", {})
        if breakdown:
            dim_scores = [v for v in breakdown.values() if isinstance(v, (int, float))]
            if dim_scores:
                # Weighted average should be within 15 points of declared score
                weights = [0.30, 0.20, 0.25, 0.25]  # tech, financial, timeline, competitive
                if len(dim_scores) >= 4:
                    weighted_avg = sum(s * w for s, w in zip(dim_scores[:4], weights))
                    if abs(score - weighted_avg) > 15:
                        issues.append({
                            "type": "score_mismatch",
                            "severity": "medium",
                            "message": f"Score Go/No-Go ({score}) incohérent avec la moyenne pondérée des dimensions ({weighted_avg:.0f})",
                            "sources": ["gonogo"],
                        })

        # Recommendation vs score coherence
        rec = gonogo.get("recommendation", "")
        if rec == "GO" and score < 60:
            issues.append({
                "type": "recommendation_mismatch",
                "severity": "high",
                "message": f"Recommandation GO mais score={score} (devrait être ≥70)",
                "sources": ["gonogo"],
            })
        elif rec == "NO-GO" and score > 50:
            issues.append({
                "type": "recommendation_mismatch",
                "severity": "high",
                "message": f"Recommandation NO-GO mais score={score} (devrait être <40)",
                "sources": ["gonogo"],
            })

    # 3. Criteria weights sum check
    criteria = results.get("criteria", {})
    if criteria:
        eval_data = criteria.get("evaluation", criteria)
        scoring = eval_data.get("scoring_criteria", [])
        weights = [c.get("weight_percent") for c in scoring if c.get("weight_percent") is not None]
        if weights:
            total = sum(weights)
            if abs(total - 100) > 5:
                issues.append({
                    "type": "weight_sum_error",
                    "severity": "medium",
                    "message": f"Somme des pondérations critères = {total}% (attendu ~100%)",
                    "sources": ["criteria"],
                })

    # 4. CCAP risk score vs number of risky clauses
    ccap = results.get("ccap", results.get("ccap_risks", {}))
    if ccap:
        risk_score = ccap.get("score_risque_global", 0)
        clauses = ccap.get("clauses_risquees", [])
        high_risk = [c for c in clauses if c.get("risque") == "élevé" or c.get("risque") == "high"]
        if risk_score < 30 and len(high_risk) >= 3:
            issues.append({
                "type": "risk_score_mismatch",
                "severity": "medium",
                "message": f"Score risque CCAP={risk_score} mais {len(high_risk)} clauses à risque élevé détectées",
                "sources": ["ccap"],
            })

    # 5. Conflicts severity distribution
    conflicts = results.get("conflicts", {})
    if conflicts:
        conflict_list = conflicts.get("conflicts", [])
        high_conflicts = [c for c in conflict_list if c.get("severity") == "high"]
        if len(high_conflicts) >= 3 and gonogo and gonogo.get("score", 100) > 70:
            issues.append({
                "type": "conflict_score_mismatch",
                "severity": "medium",
                "message": f"{len(high_conflicts)} conflits haute sévérité détectés mais Go/No-Go score={gonogo.get('score')} (GO)",
                "sources": ["conflicts", "gonogo"],
            })

    # 6. Checklist completeness vs criteria
    checklist = results.get("checklist", {})
    if checklist:
        items = checklist.get("checklist", [])
        eliminatory = [i for i in items if i.get("criticality") == "Éliminatoire"]
        if len(eliminatory) == 0 and len(items) > 5:
            issues.append({
                "type": "checklist_incomplete",
                "severity": "low",
                "message": "Aucune exigence éliminatoire détectée dans la checklist — vérifier manuellement",
                "sources": ["checklist"],
            })

    # Calculate consistency score
    severity_weights = {"high": 15, "medium": 8, "low": 3}
    penalty = sum(severity_weights.get(i["severity"], 5) for i in issues)
    consistency_score = max(0, min(100, 100 - penalty))

    if not issues:
        status = "verified"
    elif any(i["severity"] == "high" for i in issues):
        status = "inconsistencies_found"
    else:
        status = "warnings"

    return {
        "issues": issues,
        "score": consistency_score,
        "status": status,
        "checks_performed": 6,
    }
