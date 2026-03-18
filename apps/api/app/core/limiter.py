"""Rate limiter global — importé par main.py ET les routers sans import circulaire.

Try Redis first; if unreachable, fall back to in-memory storage so the app
still starts (with a warning). This avoids a hard crash when Redis is down
during development or transient outages.
"""
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

_log = logging.getLogger(__name__)


def _build_limiter() -> Limiter:
    """Create a Limiter with Redis, falling back to memory:// on failure."""
    try:
        import redis as redis_lib

        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        r.ping()
        _log.info("Rate limiter: connected to Redis (%s)", settings.REDIS_URL)
        return Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
    except Exception as exc:
        _log.warning(
            "Rate limiter: Redis unavailable (%s), falling back to in-memory storage. "
            "Rate limits will NOT be shared across workers.",
            exc,
        )
        return Limiter(key_func=get_remote_address, storage_uri="memory://")


limiter = _build_limiter()
