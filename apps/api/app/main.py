from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sentry_sdk
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
