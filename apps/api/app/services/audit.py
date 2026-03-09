"""Service d'audit RGPD — journalise les actions sensibles en base."""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = structlog.get_logger(__name__)


def log_action(
    db: Session,
    *,
    action: str,
    user_id: str | None = None,
    org_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip: str | None = None,
    extra: dict | None = None,
) -> None:
    """
    Journalise une action en base (fail silently pour ne pas casser le flux principal).

    Args:
        db:            Session SQLAlchemy synchrone.
        action:        Code action (ex: "user.login", "document.upload", "project.delete").
        user_id:       UUID de l'utilisateur (str ou None).
        org_id:        UUID de l'organisation.
        resource_type: Type de ressource (ex: "document", "project").
        resource_id:   ID de la ressource concernée.
        ip:            IP brute (sera hashée avant stockage).
        extra:         Métadonnées libres (dict JSON).
    """
    try:
        import uuid as _uuid
        entry = AuditLog(
            user_id=_uuid.UUID(user_id) if user_id else None,
            org_id=_uuid.UUID(org_id) if org_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_hash=AuditLog.hash_ip(ip),
            extra=extra,
        )
        db.add(entry)
        db.flush()  # Flush without commit (let the caller manage the transaction)
        logger.debug("audit_logged", action=action, resource_type=resource_type, resource_id=resource_id)
    except Exception as exc:
        logger.warning("audit_log_failed", action=action, error=str(exc))
        # Ne jamais propager l'erreur — l'audit ne doit pas bloquer le flux principal


def log_action_async(
    db,
    *,
    action: str,
    user_id: str | None = None,
    org_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip: str | None = None,
    extra: dict | None = None,
) -> None:
    """
    Version pour les sessions AsyncSession (FastAPI async endpoints).
    Utilise add() directement sans flush pour les sessions async.
    """
    try:
        import uuid as _uuid
        entry = AuditLog(
            user_id=_uuid.UUID(user_id) if user_id else None,
            org_id=_uuid.UUID(org_id) if org_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_hash=AuditLog.hash_ip(ip),
            extra=extra,
        )
        db.add(entry)
        logger.debug("audit_queued", action=action)
    except Exception as exc:
        logger.warning("audit_log_failed", action=action, error=str(exc))
