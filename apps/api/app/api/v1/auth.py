import re
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, create_email_verify_token, decode_token, _signing_key
from app.services.email import send_password_reset_email, send_verification_email
import structlog
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut, OrgOut, ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest
from app.api.v1.deps import get_current_user
from app.config import settings
from app.core.limiter import limiter
from app.services.audit import log_action_async

logger = structlog.get_logger(__name__)

router = APIRouter()


def slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:50]


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    # Check email unique
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    # Créer organisation
    base_slug = slugify(data.org_name)
    slug = base_slug
    # Garantir unicité du slug
    i = 1
    while True:
        exists = await db.execute(select(Organization).where(Organization.slug == slug))
        if not exists.scalar_one_or_none():
            break
        slug = f"{base_slug}-{i}"
        i += 1

    org = Organization(
        name=data.org_name,
        slug=slug,
        plan="trial",
        quota_docs=5,
        trial_expires_at=datetime.now(timezone.utc) + timedelta(days=14),
    )
    db.add(org)
    await db.flush()

    # Créer user admin
    user = User(
        org_id=org.id,
        email=data.email.lower(),
        hashed_pw=hash_password(data.password),
        full_name=data.full_name,
        role="admin",
    )
    db.add(user)
    await db.flush()

    token_data = {"sub": str(user.id), "org_id": str(org.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # httpOnly cookie pour le refresh token
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.APP_ENV != "development",
        samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    # Send verification email (fire-and-forget — don't block registration)
    verify_token = create_email_verify_token(str(user.id), user.email)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
    send_verification_email(user.email, verify_url)

    log_action_async(
        db, action="user.register",
        user_id=str(user.id), org_id=str(org.id),
        resource_type="auth",
        ip=request.client.host if request.client else None,
        extra={"email": user.email},
    )
    logger.info(
        "auth.register_success",
        user_id=str(user.id),
        email=user.email,
        org_id=str(org.id),
        ip=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_pw):
        logger.warning(
            "auth.login_failed",
            email=data.email.lower(),
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Mettre à jour last_login
    user.last_login_at = datetime.now(timezone.utc)

    token_data = {"sub": str(user.id), "org_id": str(user.org_id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.APP_ENV != "development",
        samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    log_action_async(
        db, action="user.login",
        user_id=str(user.id), org_id=str(user.org_id),
        resource_type="auth",
        ip=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token manquant")

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expiré ou invalide")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token invalide (type incorrect)")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    token_data = {"sub": str(user.id), "org_id": str(user.org_id), "role": user.role}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    response.set_cookie(
        key="refresh_token", value=new_refresh,
        httponly=True, secure=settings.APP_ENV != "development",
        samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    logger.info(
        "auth.token_refresh",
        user_id=str(user.id),
        org_id=str(user.org_id),
    )
    return TokenResponse(access_token=new_access, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=UserOut)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    # Construire un dict pour enrichir le user avec org_slug et onboarding_completed
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "org_id": current_user.org_id,
        "org_slug": org.slug if org else None,
        "onboarding_completed": org.onboarding_completed if org else True,
        "email_verified": current_user.email_verified,
    }
    return user_dict


@router.post("/verify-email")
@limiter.limit("10/minute")
async def verify_email(request: Request, data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify user email address using the token sent after registration."""
    try:
        payload = decode_token(data.token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Lien de vérification invalide ou expiré")

    if payload.get("type") != "email_verify":
        raise HTTPException(status_code=400, detail="Token invalide (type incorrect)")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token invalide")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Utilisateur introuvable")

    if user.email_verified:
        return {"message": "Email déjà vérifié"}

    user.email_verified = True
    await db.flush()

    log_action_async(
        db, action="user.email_verified",
        user_id=str(user.id), org_id=str(user.org_id),
        resource_type="auth",
        ip=request.client.host if request.client else None,
    )

    return {"message": "Email vérifié avec succès"}


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email for the current logged-in user."""
    if current_user.email_verified:
        return {"message": "Email déjà vérifié"}

    verify_token = create_email_verify_token(str(current_user.id), current_user.email)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
    send_verification_email(current_user.email, verify_url)

    return {"message": "Email de vérification envoyé"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Envoie un email de réinitialisation. Retourne toujours 200 (ne révèle pas si l'email existe)."""
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()

    if user:
        # Générer un JWT reset (15 min, type="reset")
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        reset_payload = {"sub": str(user.id), "type": "reset", "exp": expire}
        reset_token = jwt.encode(reset_payload, _signing_key(), algorithm=settings.JWT_ALGORITHM)

        reset_url = f"{settings.FRONTEND_URL}/login/reset-password?token={reset_token}"
        send_password_reset_email(user.email, reset_url)

        log_action_async(
            db, action="user.forgot_password",
            user_id=str(user.id), org_id=str(user.org_id),
            resource_type="auth",
            ip=request.client.host if request.client else None,
        )
    else:
        logger.info("forgot_password_unknown_email", email=data.email.lower())

    return {"message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Réinitialise le mot de passe avec un token valide."""
    try:
        payload = decode_token(data.token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Lien de réinitialisation invalide ou expiré")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Token invalide (type incorrect)")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token invalide")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Utilisateur introuvable")

    # Mettre à jour le mot de passe
    user.hashed_pw = hash_password(data.new_password)
    await db.flush()

    log_action_async(
        db, action="user.reset_password",
        user_id=str(user.id), org_id=str(user.org_id),
        resource_type="auth",
        ip=request.client.host if request.client else None,
    )

    return {"message": "Mot de passe réinitialisé avec succès"}
