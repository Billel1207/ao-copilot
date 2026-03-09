"""Service de livraison des webhooks AO Copilot.

Envoie des événements HTTP POST signés HMAC-SHA256 vers les endpoints configurés.
"""
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timezone
import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = structlog.get_logger()

WEBHOOK_EVENTS = [
    "analysis.completed",      # Analyse IA terminée
    "project.created",         # Nouveau projet créé
    "project.deadline_due",    # Deadline dans 7 jours
    "quota.warning",           # Quota à 80%
    "subscription.changed",    # Plan upgradé/annulé
    "test.ping",               # Événement de test de connectivité
]


def _sign_payload(secret: str, payload: str) -> str:
    """Génère la signature HMAC-SHA256 du payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def dispatch_webhook(
    db: AsyncSession,
    org_id: str,
    event_type: str,
    payload: dict,
) -> None:
    """
    Dispatche un événement webhook à tous les endpoints actifs de l'org.
    Appelé de manière async depuis les tasks Celery ou les routes API.
    """
    from app.models.webhook import WebhookEndpoint, WebhookDelivery

    # Récupérer les endpoints actifs pour cet event
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.org_id == uuid.UUID(org_id),
            WebhookEndpoint.is_active == True,  # noqa: E712
        )
    )
    endpoints = result.scalars().all()

    # Filtrer par événement souscrit
    matching = [
        ep for ep in endpoints
        if event_type in ep.events.split(",")
    ]

    if not matching:
        return

    # Préparer le payload JSON
    event_payload = {
        "id": str(uuid.uuid4()),
        "event": event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "org_id": org_id,
        "data": payload,
    }
    payload_json = json.dumps(event_payload, default=str)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in matching:
            signature = _sign_payload(endpoint.secret, payload_json)
            delivery_success = False
            status_code = None
            error_msg = None

            try:
                resp = await client.post(
                    endpoint.url,
                    content=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-AO-Event": event_type,
                        "X-AO-Signature": f"sha256={signature}",
                        "X-AO-Delivery": event_payload["id"],
                        "User-Agent": "AO-Copilot-Webhooks/1.0",
                    },
                )
                status_code = resp.status_code
                delivery_success = 200 <= resp.status_code < 300

                if not delivery_success:
                    error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    endpoint.failure_count = (endpoint.failure_count or 0) + 1
                else:
                    endpoint.failure_count = 0
                    endpoint.last_delivery_at = datetime.now(timezone.utc)

            except httpx.TimeoutException:
                error_msg = "Timeout (10s)"
                endpoint.failure_count = (endpoint.failure_count or 0) + 1
            except Exception as e:
                error_msg = str(e)[:200]
                endpoint.failure_count = (endpoint.failure_count or 0) + 1

            # Désactiver après 10 échecs consécutifs
            if endpoint.failure_count >= 10:
                endpoint.is_active = False
                logger.warning(
                    "webhook_endpoint_auto_disabled",
                    endpoint_id=str(endpoint.id),
                    url=endpoint.url,
                )

            # Log la livraison
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_type=event_type,
                payload=payload_json,
                status_code=status_code,
                success=delivery_success,
                error_message=error_msg,
            )
            db.add(delivery)

            logger.info(
                "webhook_dispatched",
                event=event_type,
                endpoint_id=str(endpoint.id),
                success=delivery_success,
                status_code=status_code,
            )

    await db.commit()
