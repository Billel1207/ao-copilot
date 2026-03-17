import uuid
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Organization

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
