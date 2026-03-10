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


async def dispatch_event(
    db: AsyncSession,
    org_id: str,
    event_type: str,
    data: dict,
) -> int:
    """Envoie un événement à tous les endpoints actifs de l'organisation.

    Returns:
        Nombre d'endpoints notifiés avec succès.
    """
    import uuid

    # Récupérer les endpoints actifs qui écoutent cet événement
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.org_id == uuid.UUID(str(org_id)),
            WebhookEndpoint.is_active == True,
            WebhookEndpoint.failure_count < MAX_FAILURE_COUNT,
        )
    )
    endpoints = result.scalars().all()

    if not endpoints:
        return 0

    # Construire le payload
    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)

    success_count = 0

    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
        for endpoint in endpoints:
            # Vérifier que l'endpoint écoute cet événement
            subscribed_events = [e.strip() for e in endpoint.events.split(",")]
            if event_type not in subscribed_events:
                continue

            # SSRF protection : vérifier que l'URL ne pointe pas vers un réseau privé
            if not _is_safe_url(endpoint.url):
                logger.warning(
                    "webhook_skipped_unsafe_url",
                    endpoint_url=endpoint.url,
                    event=event_type,
                )
                continue

            # Signer le payload
            signature = _sign_payload(payload_json, endpoint.secret)

            # Livrer
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_type=event_type,
                payload=payload_json,
                attempt_number=1,
            )

            try:
                resp = await client.post(
                    endpoint.url,
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
                    endpoint.failure_count = 0
                    success_count += 1
                else:
                    endpoint.failure_count += 1
                    delivery.error_message = f"HTTP {resp.status_code}"

            except httpx.TimeoutException:
                delivery.success = False
                delivery.error_message = "Timeout"
                endpoint.failure_count += 1
            except Exception as exc:
                delivery.success = False
                delivery.error_message = str(exc)[:500]
                endpoint.failure_count += 1

            endpoint.last_delivery_at = datetime.now(timezone.utc)
            db.add(delivery)

            logger.info(
                "webhook_delivered",
                endpoint_url=endpoint.url,
                event=event_type,
                success=delivery.success,
                status_code=delivery.status_code,
            )

    await db.flush()
    return success_count
