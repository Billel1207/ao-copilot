import hashlib
import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Organization
from app.models.api_key import ApiKey

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    access_token: str | None = Cookie(default=None),
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token invalide")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expiré ou invalide")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


async def get_current_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=403, detail="Organisation introuvable ou désactivée")
    return org


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")
    return current_user


def get_llm_service():
    """Dependency injection pour le service LLM.

    Retourne le singleton LLMService. L'injection via Depends() permet
    de mocker facilement dans les tests : app.dependency_overrides[get_llm_service] = lambda: MockLLM()
    """
    from app.services.llm import llm_service
    return llm_service


# ── API Key authentication ──────────────────────────────────────────────

# Mapping des noms de scope vers les colonnes du modèle ApiKey
SCOPE_COLUMN_MAP = {
    "read:projects": "can_read_projects",
    "write:projects": "can_write_projects",
    "read:analysis": "can_read_analysis",
    "trigger:analysis": "can_trigger_analysis",
    "manage:billing": "can_manage_billing",
    "export": "can_export",
}


async def authenticate_api_key(
    db: AsyncSession = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ApiKey | None:
    """Authentifie une requête par clé API (header X-API-Key).

    Retourne None si aucune clé n'est fournie (fallback vers JWT).
    Lève 401/403 si la clé est invalide, révoquée ou expirée.
    """
    if not x_api_key:
        return None

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=401, detail="Clé API invalide")

    if not api_key.is_active or api_key.revoked_at is not None:
        raise HTTPException(status_code=403, detail="Clé API révoquée")

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Clé API expirée")

    # Mettre à jour last_used_at
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.flush()

    return api_key


def require_api_scope(*scopes: str) -> Callable:
    """Factory de dépendance qui vérifie qu'une clé API possède les scopes requis.

    Usage dans une route :
        @router.get("/projects", dependencies=[Depends(require_api_scope("read:projects"))])

    Si l'auth est par JWT (pas de X-API-Key), la vérification est bypassée
    car l'utilisateur humain a tous les droits de son rôle.
    """
    async def _check_scope(
        api_key: ApiKey | None = Depends(authenticate_api_key),
    ):
        if api_key is None:
            # Auth JWT — pas de restriction de scope API key
            return

        for scope in scopes:
            column_name = SCOPE_COLUMN_MAP.get(scope)
            if not column_name:
                raise HTTPException(
                    status_code=500,
                    detail=f"Scope inconnu : {scope}",
                )
            if not getattr(api_key, column_name, False):
                raise HTTPException(
                    status_code=403,
                    detail=f"Clé API : permission '{scope}' requise",
                )

    return _check_scope
