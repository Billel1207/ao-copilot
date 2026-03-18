"""Service de dispatch des webhooks — envoie les événements aux endpoints configurés.

Événements supportés :
- analysis.completed  : analyse terminée pour un projet
- project.created     : nouveau projet créé
- project.deadline_due: date limite dans <7 jours
- quota.warning       : >80% du quota mensuel utilisé
"""
import json
import hmac
import hashlib
import ipaddress
import os
import socket
import structlog
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.webhook import WebhookEndpoint, WebhookDelivery

logger = structlog.get_logger(__name__)

WEBHOOK_TIMEOUT = 10  # secondes
MAX_FAILURE_COUNT = 10  # désactive après 10 échecs consécutifs

# Réseaux privés / loopback interdits pour les webhooks (protection SSRF)
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_safe_url(url: str) -> bool:
    """Vérifie qu'une URL webhook ne pointe pas vers un réseau privé/loopback (SSRF).

    Autorise uniquement HTTPS en production. HTTP est toléré en développement.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Schéma : HTTPS obligatoire sauf en dev
    is_dev = os.environ.get("ENV", "production").lower() in ("development", "dev", "local")
    if parsed.scheme != "https" and not (is_dev and parsed.scheme == "http"):
        logger.warning("webhook_blocked_scheme", url=url, scheme=parsed.scheme)
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    # Résoudre le hostname vers ses adresses IP
    try:
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        logger.warning("webhook_dns_resolution_failed", hostname=hostname)
        return False

    for addr_info in addr_infos:
        ip = ipaddress.ip_address(addr_info[4][0])
        for network in _BLOCKED_NETWORKS:
            if ip in network:
                logger.warning(
                    "webhook_blocked_private_ip",
                    url=url,
                    hostname=hostname,
                    resolved_ip=str(ip),
                    network=str(network),
                )
                return False

    return True


def _sign_payload(payload_json: str, secret: str) -> str:
    """Génère la signature HMAC-SHA256 du payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def get_subscribed_endpoints(
    db: AsyncSession,
    org_id: str,
    event_type: str,
) -> list[dict]:
    """Récupère les endpoints actifs abonnés à un événement.

    Returns:
        Liste de dicts {endpoint_id, url, secret} pour chaque endpoint éligible.
    """
    import uuid

    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.org_id == uuid.UUID(str(org_id)),
            WebhookEndpoint.is_active == True,
            WebhookEndpoint.failure_count < MAX_FAILURE_COUNT,
        )
    )
    endpoints = result.scalars().all()

    eligible = []
    for ep in endpoints:
        subscribed_events = [e.strip() for e in ep.events.split(",")]
        if event_type not in subscribed_events:
            continue
        if not _is_safe_url(ep.url):
            logger.warning("webhook_skipped_unsafe_url", endpoint_url=ep.url, event=event_type)
            continue
        eligible.append({
            "endpoint_id": str(ep.id),
            "url": ep.url,
            "secret": ep.secret,
        })

    return eligible


def deliver_single_webhook_sync(
    endpoint_id: str,
    url: str,
    secret: str,
    event_type: str,
    payload_json: str,
    attempt_number: int,
) -> dict:
    """Livre un webhook à un endpoint unique (synchrone, pour Celery).

    Returns:
        Dict avec status de la livraison.
    """
    import uuid
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
    from app.config import settings

    signature = _sign_payload(payload_json, secret)

    status_code = None
    success = False
    error_message = None

    try:
        import httpx as _httpx
        with _httpx.Client(timeout=WEBHOOK_TIMEOUT) as client:
            resp = client.post(
                url,
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-AO-Copilot-Signature": f"sha256={signature}",
                    "X-AO-Copilot-Event": event_type,
                },
            )
            status_code = resp.status_code
            success = 200 <= resp.status_code < 300
            if not success:
                error_message = f"HTTP {resp.status_code}"
    except Exception as exc:
        error_message = str(exc)[:500]

    # Persister le résultat en DB (session synchrone pour Celery)
    engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", ""),
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        delivery = WebhookDelivery(
            endpoint_id=uuid.UUID(endpoint_id),
            event_type=event_type,
            payload=payload_json,
            attempt_number=attempt_number,
            status_code=status_code,
            success=success,
            error_message=error_message,
        )
        db.add(delivery)

        ep = db.get(WebhookEndpoint, uuid.UUID(endpoint_id))
        if ep:
            ep.last_delivery_at = datetime.now(timezone.utc)
            if success:
                ep.failure_count = 0
            else:
                ep.failure_count = (ep.failure_count or 0) + 1

        db.commit()
    finally:
        db.close()
        engine.dispose()

    logger.info(
        "webhook_delivered",
        endpoint_url=url,
        event=event_type,
        success=success,
        status_code=status_code,
        attempt=attempt_number,
    )

    return {"success": success, "status_code": status_code, "error": error_message}


# Legacy — conservé pour rétro-compatibilité mais déprécié
async def dispatch_event(
    db: AsyncSession,
    org_id: str,
    event_type: str,
    data: dict,
) -> int:
    """[DEPRECATED] Utilisez dispatch_webhook_event (Celery fan-out) à la place.

    Conservé pour les appels directs en mode test.
    """
    endpoints = await get_subscribed_endpoints(db, org_id, event_type)
    if not endpoints:
        return 0

    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)

    success_count = 0
    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
        for ep in endpoints:
            signature = _sign_payload(payload_json, ep["secret"])
            delivery = WebhookDelivery(
                endpoint_id=__import__("uuid").UUID(ep["endpoint_id"]),
                event_type=event_type,
                payload=payload_json,
                attempt_number=1,
            )
            try:
                resp = await client.post(
                    ep["url"],
                    content=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-AO-Copilot-Signature": f"sha256={signature}",
                        "X-AO-Copilot-Event": event_type,
                    },
                )
                delivery.status_code = resp.status_code
                delivery.success = 200 <= resp.status_code < 300
                if delivery.success:
                    success_count += 1
                else:
                    delivery.error_message = f"HTTP {resp.status_code}"
            except Exception as exc:
                delivery.success = False
                delivery.error_message = str(exc)[:500]

            db.add(delivery)

    await db.flush()
    return success_count
