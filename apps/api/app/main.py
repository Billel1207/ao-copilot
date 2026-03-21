from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sentry_sdk
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from urllib.parse import urlparse
from app.config import settings
from app.core.limiter import limiter
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.export import router as export_router
from app.api.v1.billing import router as billing_router
from app.api.v1.team import router as team_router
from app.api.v1.library import router as library_router
from app.api.v1.annotations import router as annotations_router
from app.api.v1.veille import router as veille_router
from app.api.v1.company import router as company_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.attestations import router as attestations_router
from app.api.v1.developer import router as developer_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.sso import router as sso_router
from app.api.v1.gdpr import router as gdpr_router

import structlog


def _configure_structlog():
    """Configure structlog : JSON en production, console colorée en dev."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.APP_ENV == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _configure_structlog()
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.APP_ENV)
    yield
    # Shutdown (cleanup si besoin)


app = FastAPI(
    title="AO Copilot API",
    description="Analyse automatique de DCE (Appels d'Offres BTP)",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate limiting — 429 Too Many Requests sur dépassement
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "Cookie"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ── CSRF protection middleware (double-submit Origin check) ──────────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# Paths exempt from CSRF check (public auth endpoints + Stripe webhook)
_CSRF_EXEMPT_PATHS: set[str] = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/webhooks/stripe",
}

_STATE_CHANGING_METHODS: set[str] = {"POST", "PUT", "DELETE", "PATCH"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests whose Origin/Referer doesn't match allowed origins.

    This is the standard 'Origin check' CSRF mitigation recommended by OWASP.
    Requests without an Origin or Referer header are also rejected for
    state-changing methods (except exempt paths).
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in _STATE_CHANGING_METHODS:
            return await call_next(request)

        # Skip exempt endpoints
        if request.url.path in _CSRF_EXEMPT_PATHS:
            return await call_next(request)

        origin = request.headers.get("origin") or request.headers.get("referer")
        if not origin:
            return StarletteResponse(
                content='{"detail":"Missing Origin header"}',
                status_code=403,
                media_type="application/json",
            )

        # Normalise: extract scheme + host from origin/referer
        parsed = urlparse(origin)
        request_origin = f"{parsed.scheme}://{parsed.netloc}"

        allowed = settings.allowed_origins_list
        if request_origin not in allowed:
            return StarletteResponse(
                content='{"detail":"Origin not allowed"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


app.add_middleware(CSRFMiddleware)


# ── Security headers middleware ──────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every API response.

    These headers complement the nginx layer (CSP, HSTS) with
    API-specific protections that work even in dev (no nginx).

    Cache-Control strategy:
    - Auth/mutation endpoints → no-store (default)
    - Health checks → public, 10s (monitoring tools)
    - Static reference data (glossary, certifications, CPV) → private, 5min
    - Analytics/stats → private, 1min
    """

    # Cacheable GET prefixes → (max-age seconds, public?)
    _CACHEABLE_PREFIXES: list[tuple[str, int, bool]] = [
        ("/api/health", 10, True),
        ("/api/v1/knowledge/glossary", 300, False),
        ("/api/v1/knowledge/certifications", 300, False),
        ("/api/v1/knowledge/cpv", 300, False),
        ("/api/v1/knowledge/thresholds", 300, False),
        ("/api/v1/analytics/", 60, False),
    ]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Smart Cache-Control: allow caching for read-only reference endpoints
        cache_set = False
        if request.method == "GET":
            path = request.url.path
            for prefix, max_age, is_public in self._CACHEABLE_PREFIXES:
                if path.startswith(prefix):
                    scope = "public" if is_public else "private"
                    response.headers["Cache-Control"] = f"{scope}, max-age={max_age}"
                    cache_set = True
                    break

        if not cache_set:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response

app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(documents_router, prefix="/api/v1/projects", tags=["documents"])
app.include_router(analysis_router, prefix="/api/v1/projects", tags=["analysis"])
app.include_router(export_router, prefix="/api/v1/projects", tags=["export"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(team_router, prefix="/api/v1/team", tags=["team"])
app.include_router(library_router, prefix="/api/v1/library", tags=["library"])
app.include_router(annotations_router, prefix="/api/v1/projects", tags=["annotations"])
app.include_router(veille_router, prefix="/api/v1/veille", tags=["veille"])
app.include_router(company_router, prefix="/api/v1/company", tags=["company"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(onboarding_router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(attestations_router, prefix="/api/v1/attestations", tags=["attestations"])
app.include_router(developer_router, prefix="/api/v1/developer", tags=["developer"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["api-keys"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(sso_router, prefix="/api/v1/sso", tags=["sso"])
app.include_router(gdpr_router, prefix="/api/v1/account", tags=["gdpr"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/health/ready")
async def health_ready():
    """Deep healthcheck — vérifie DB + Redis. Utilisé par monitoring / load balancer."""
    import time
    from app.core.database import SyncSessionLocal
    checks: dict = {"api": "ok", "version": "0.1.0"}
    start = time.monotonic()

    # Check PostgreSQL
    try:
        db = SyncSessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "error"

    # Check Redis / Celery broker
    try:
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "error"

    checks["latency_ms"] = round((time.monotonic() - start) * 1000, 1)
    all_ok = checks.get("database") == "ok" and checks.get("redis") == "ok"
    checks["status"] = "ok" if all_ok else "degraded"

    return JSONResponse(content=checks, status_code=200 if all_ok else 503)
