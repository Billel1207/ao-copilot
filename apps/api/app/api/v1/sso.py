"""Routes SSO SAML pour le plan Business.

Flux SAML 2.0 simplifié :
1. L'admin configure l'IDP (metadata_url, entity_id) via PUT /sso/config
2. Les users se connectent via GET /sso/login → redirect vers IDP
3. L'IDP POST la réponse SAML vers /sso/callback → on crée/connecte le user

Dépendance : pip install python3-saml>=1.16.0
"""
import uuid
import secrets
import time
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────

class SsoConfigIn(BaseModel):
    idp_entity_id: str = Field(..., max_length=500, description="Entity ID de l'IDP (ex: https://idp.example.com)")
    idp_sso_url: str = Field(..., max_length=500, description="URL de login SSO de l'IDP")
    idp_certificate: str = Field(..., description="Certificat X.509 de l'IDP (PEM)")
    idp_slo_url: str | None = Field(None, max_length=500, description="URL de logout (optionnel)")


class SsoConfigOut(BaseModel):
    enabled: bool
    idp_entity_id: str | None
    idp_sso_url: str | None
    sp_entity_id: str
    sp_acs_url: str
    created_at: str | None


class SsoStatusOut(BaseModel):
    sso_enabled: bool
    plan: str
    message: str


class SsoExchangeIn(BaseModel):
    sso_code: str = Field(..., description="One-time SSO exchange code")


# ── One-time SSO code store (in-memory, short-lived) ─────────────────────
_SSO_CODES: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────

def _check_business_plan(org: Organization):
    if org.plan != "business":
        raise HTTPException(
            status_code=403,
            detail="SSO SAML est disponible uniquement sur le plan Business (499€/mois).",
        )


def _get_sp_entity_id(org: Organization) -> str:
    """Service Provider Entity ID unique par organisation."""
    return f"{settings.FRONTEND_URL}/sso/{org.slug or org.id}"


def _get_sp_acs_url(org: Organization) -> str:
    """Assertion Consumer Service URL — là où l'IDP envoie la réponse SAML."""
    base = settings.FRONTEND_URL.replace("http://localhost:3000", settings.BACKEND_URL if hasattr(settings, 'BACKEND_URL') else "http://localhost:8000")
    return f"{base}/api/v1/sso/callback?org_id={org.id}"


def _build_saml_settings(org: Organization) -> dict:
    """Construit la configuration python3-saml pour l'organisation."""
    sp_entity_id = _get_sp_entity_id(org)
    acs_url = _get_sp_acs_url(org)

    return {
        "strict": True,
        "debug": settings.APP_ENV != "production",
        "sp": {
            "entityId": sp_entity_id,
            "assertionConsumerService": {
                "url": acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": getattr(org, "sso_idp_entity_id", "") or "",
            "singleSignOnService": {
                "url": getattr(org, "sso_idp_sso_url", "") or "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": getattr(org, "sso_idp_slo_url", "") or "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": getattr(org, "sso_idp_certificate", "") or "",
        },
        "security": {
            "wantAssertionsSigned": True,
            "wantNameIdEncrypted": False,
        },
    }


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/status", response_model=SsoStatusOut)
async def sso_status(
    org: Organization = Depends(get_current_org),
):
    """Vérifie si SSO est disponible et configuré pour l'organisation."""
    if org.plan != "business":
        return SsoStatusOut(
            sso_enabled=False,
            plan=org.plan,
            message="SSO SAML nécessite le plan Business.",
        )

    sso_configured = bool(getattr(org, "sso_idp_entity_id", None))
    return SsoStatusOut(
        sso_enabled=sso_configured,
        plan=org.plan,
        message="SSO configuré et actif." if sso_configured else "SSO disponible mais non configuré.",
    )


@router.get("/config", response_model=SsoConfigOut)
async def get_sso_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne la configuration SSO actuelle."""
    _check_business_plan(org)

    return SsoConfigOut(
        enabled=bool(getattr(org, "sso_idp_entity_id", None)),
        idp_entity_id=getattr(org, "sso_idp_entity_id", None),
        idp_sso_url=getattr(org, "sso_idp_sso_url", None),
        sp_entity_id=_get_sp_entity_id(org),
        sp_acs_url=_get_sp_acs_url(org),
        created_at=None,
    )


@router.put("/config", response_model=SsoConfigOut)
async def update_sso_config(
    body: SsoConfigIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Configure ou met à jour les paramètres SSO SAML."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut configurer SSO")

    # Stocker la config SSO sur l'organisation
    org.sso_idp_entity_id = body.idp_entity_id
    org.sso_idp_sso_url = body.idp_sso_url
    org.sso_idp_certificate = body.idp_certificate
    org.sso_idp_slo_url = body.idp_slo_url
    await db.flush()

    logger.info("sso_config_updated", org_id=str(org.id))

    return SsoConfigOut(
        enabled=True,
        idp_entity_id=body.idp_entity_id,
        idp_sso_url=body.idp_sso_url,
        sp_entity_id=_get_sp_entity_id(org),
        sp_acs_url=_get_sp_acs_url(org),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/login")
async def sso_login(
    request: Request,
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Initie le flux SSO SAML — redirige vers l'IDP."""
    org_result = await db.execute(
        select(Organization).where(Organization.id == uuid.UUID(org_id))
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    _check_business_plan(org)

    idp_sso_url = getattr(org, "sso_idp_sso_url", None)
    if not idp_sso_url:
        raise HTTPException(status_code=400, detail="SSO non configuré pour cette organisation")

    # Construire la requête SAML AuthnRequest avec python3-saml
    saml_settings = _build_saml_settings(org)

    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
        saml_req = {
            "http_host": request.url.hostname,
            "script_name": str(request.url.path),
            "get_data": dict(request.query_params),
            "post_data": {},
            "https": "on" if settings.APP_ENV == "production" else "off",
        }
        auth = OneLogin_Saml2_Auth(saml_req, saml_settings)
        redirect_url = auth.login(return_to=f"{settings.FRONTEND_URL}/dashboard")
    except ImportError:
        # Fallback si python3-saml n'est pas installé (dev mode)
        logger.warning("python3-saml not installed — using basic redirect")
        redirect_url = (
            f"{idp_sso_url}"
            f"?RelayState={settings.FRONTEND_URL}/dashboard"
        )

    logger.info("sso_login_initiated", org_id=str(org.id))
    return RedirectResponse(url=redirect_url)


@router.post("/callback")
async def sso_callback(
    request: Request,
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Reçoit la réponse SAML de l'IDP et connecte le user.

    En production, cette route :
    1. Valide la signature SAML avec le certificat IDP
    2. Extrait email + attributs du user
    3. Crée le user s'il n'existe pas (auto-provisioning)
    4. Génère un JWT et redirige vers le frontend
    """
    form = await request.form()
    saml_response = form.get("SAMLResponse")
    relay_state = form.get("RelayState", f"{settings.FRONTEND_URL}/dashboard")

    # Fix 2: Validate relay_state against FRONTEND_URL to prevent open redirect
    if not relay_state or not relay_state.startswith(settings.FRONTEND_URL):
        relay_state = f"{settings.FRONTEND_URL}/dashboard"

    if not saml_response:
        raise HTTPException(status_code=400, detail="SAMLResponse manquant")

    org_result = await db.execute(
        select(Organization).where(Organization.id == uuid.UUID(org_id))
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    # Valider la réponse SAML avec python3-saml
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        saml_settings = _build_saml_settings(org)
        saml_req = {
            "http_host": request.url.hostname,
            "script_name": str(request.url.path),
            "get_data": dict(request.query_params),
            "post_data": {"SAMLResponse": saml_response, "RelayState": relay_state},
            "https": "on" if settings.APP_ENV == "production" else "off",
        }
        auth = OneLogin_Saml2_Auth(saml_req, saml_settings)
        auth.process_response()
        errors = auth.get_errors()

        if errors:
            logger.error("sso_saml_validation_failed", errors=errors, org_id=str(org.id))
            raise HTTPException(status_code=400, detail=f"Erreur validation SAML: {', '.join(errors)}")

        if not auth.is_authenticated():
            raise HTTPException(status_code=401, detail="Authentification SAML échouée")

        # Extraire les attributs du user depuis la réponse SAML
        saml_attrs = auth.get_attributes()
        saml_email = (
            auth.get_nameid()
            or saml_attrs.get("email", [None])[0]
            or saml_attrs.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", [None])[0]
        )

        if not saml_email:
            raise HTTPException(status_code=400, detail="Email non trouvé dans la réponse SAML")

        # Auto-provisioning : créer le user s'il n'existe pas
        user_result = await db.execute(
            select(User).where(User.email == saml_email.lower())
        )
        user = user_result.scalar_one_or_none()

        if not user:
            user = User(
                email=saml_email.lower(),
                full_name=saml_attrs.get("displayName", [saml_email.split("@")[0]])[0],
                org_id=org.id,
                role="member",
                hashed_password="SSO_MANAGED",
                is_active=True,
            )
            db.add(user)
            await db.flush()
            logger.info("sso_user_auto_provisioned", email=saml_email, org_id=str(org.id))

        # Générer un JWT pour le user
        from app.core.security import create_access_token, create_refresh_token
        token_data = {"sub": str(user.id), "org_id": str(user.org_id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        logger.info("sso_callback_success", email=saml_email, org_id=str(org.id))

        # Fix 3: Store tokens behind a short-lived one-time code (never in URL)
        sso_code = secrets.token_urlsafe(32)
        _SSO_CODES[sso_code] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": time.time() + 30,  # 30-second TTL
        }
        redirect = f"{relay_state}?sso_code={sso_code}"
        return RedirectResponse(url=redirect, status_code=303)

    except ImportError:
        logger.warning("python3-saml not installed — SSO callback cannot validate")
        raise HTTPException(status_code=503, detail="SSO non disponible — python3-saml requis")


@router.post("/exchange")
async def sso_exchange(
    body: SsoExchangeIn,
    response: Response,
):
    """Exchange a one-time SSO code for session tokens.

    The code is valid for 30 seconds and can only be used once.
    Tokens are returned as httpOnly cookies (same pattern as /login).
    """
    # Purge expired codes (lazy cleanup)
    now = time.time()
    expired_keys = [k for k, v in _SSO_CODES.items() if v["expires_at"] < now]
    for k in expired_keys:
        del _SSO_CODES[k]

    entry = _SSO_CODES.pop(body.sso_code, None)
    if not entry:
        raise HTTPException(status_code=400, detail="Code SSO invalide ou expiré")

    if entry["expires_at"] < now:
        raise HTTPException(status_code=400, detail="Code SSO expiré")

    # Set refresh token as httpOnly cookie (same as login endpoint)
    response.set_cookie(
        key="refresh_token",
        value=entry["refresh_token"],
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return {
        "access_token": entry["access_token"],
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.delete("/config")
async def disable_sso(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Désactive SSO SAML pour l'organisation."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut désactiver SSO")

    org.sso_idp_entity_id = None
    org.sso_idp_sso_url = None
    org.sso_idp_certificate = None
    org.sso_idp_slo_url = None
    await db.flush()

    logger.info("sso_disabled", org_id=str(org.id))
    return {"status": "disabled"}
