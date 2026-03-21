"""AI Audit Logger — Logs every LLM call for AI Act Article 50 compliance.

Usage (in analyzers or any service that calls LLM):

    from app.services.ai_audit_logger import log_ai_call

    result = llm_service.complete_json(system, user)
    usage = llm_service.get_usage_summary()
    log_ai_call(
        db=db,
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        task_type="ccap_analysis",
        input_tokens=usage["total_input"],
        output_tokens=usage["total_output"],
        cached_tokens=usage["total_cached"],
        latency_ms=elapsed_ms,
        prompt_hash=AIAuditLog.hash_prompt(user_prompt),
        project_id=project_id,
        org_id=org_id,
    )
"""
import structlog
from typing import Any
from sqlalchemy.orm import Session

from app.models.ai_audit import AIAuditLog

logger = structlog.get_logger(__name__)


def log_ai_call(
    db: Session,
    *,
    provider: str,
    model: str,
    task_type: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cached_tokens: int | None = None,
    latency_ms: float | None = None,
    prompt_hash: str | None = None,
    success: bool = True,
    error_type: str | None = None,
    org_id: Any | None = None,
    user_id: Any | None = None,
    project_id: Any | None = None,
    extra: dict | None = None,
) -> None:
    """Log a single LLM call to the ai_audit_logs table.

    This function is fire-and-forget: errors are logged but never raised,
    to avoid disrupting the main analysis pipeline.
    """
    try:
        entry = AIAuditLog(
            provider=provider,
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            latency_ms=latency_ms,
            prompt_hash=prompt_hash,
            success=success,
            error_type=error_type,
            org_id=org_id,
            user_id=user_id,
            project_id=project_id,
            extra=extra,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.warning("ai_audit_log_failed", error=str(exc), task_type=task_type)
        try:
            db.rollback()
        except Exception:
            pass
