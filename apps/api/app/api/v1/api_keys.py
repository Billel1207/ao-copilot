"""Routes API pour la gestion des clés API (plan Business uniquement).

CRUD complet : créer, lister, révoquer des clés API.
Chaque clé est stockée hashée (SHA-256) — la clé complète n'est visible qu'à la création.
"""
import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────

class ApiKeyCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    can_read_projects: bool = True
    can_write_projects: bool = False
    can_read_analysis: bool = True
    can_trigger_analysis: bool = False


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    can_read_projects: bool
    can_write_projects: bool
    can_read_analysis: bool
    can_trigger_analysis: bool
    is_active: bool
    last_used_at: str | None
    created_at: str


class ApiKeyCreatedOut(ApiKeyOut):
    """Retourné uniquement à la création — contient la clé complète."""
    full_key: str


# ── Helpers ───────────────────────────────────────────────────────────────

def _generate_api_key() -> tuple[str, str, str]:
    """Génère une clé API, son préfixe et son hash SHA-256."""
    raw = secrets.token_urlsafe(32)
    full_key = f"aoc_{raw}"
    prefix = full_key[:10]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def _check_business_plan(org: Organization):
    """Vérifie que l'organisation est sur le plan Business."""
    if org.plan != "business":
        raise HTTPException(
            status_code=403,
            detail="Les clés API sont disponibles uniquement sur le plan Business (499€/mois).",
        )


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Liste toutes les clés API de l'organisation."""
    _check_business_plan(org)

    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.org_id == org.id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        ApiKeyOut(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            can_read_projects=k.can_read_projects,
            can_write_projects=k.can_write_projects,
            can_read_analysis=k.can_read_analysis,
            can_trigger_analysis=k.can_trigger_analysis,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.post("", response_model=ApiKeyCreatedOut, status_code=201)
async def create_api_key(
    body: ApiKeyCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée une nouvelle clé API. La clé complète n'est visible qu'une seule fois."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut créer des clés API")

    # Limite : max 10 clés actives par org
    count_result = await db.execute(
        select(ApiKey).where(
            ApiKey.org_id == org.id,
            ApiKey.revoked_at.is_(None),
            ApiKey.is_active == True,
        )
    )
    if len(count_result.scalars().all()) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 clés API actives par organisation")

    full_key, prefix, key_hash = _generate_api_key()

    api_key = ApiKey(
        org_id=org.id,
        created_by=current_user.id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        can_read_projects=body.can_read_projects,
        can_write_projects=body.can_write_projects,
        can_read_analysis=body.can_read_analysis,
        can_trigger_analysis=body.can_trigger_analysis,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    logger.info("api_key_created", key_prefix=prefix, org_id=str(org.id))

    return ApiKeyCreatedOut(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        full_key=full_key,
        can_read_projects=api_key.can_read_projects,
        can_write_projects=api_key.can_write_projects,
        can_read_analysis=api_key.can_read_analysis,
        can_trigger_analysis=api_key.can_trigger_analysis,
        is_active=api_key.is_active,
        last_used_at=None,
        created_at=api_key.created_at.isoformat(),
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Révoque une clé API (soft-delete)."""
    _check_business_plan(org)

    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut révoquer des clés API")

    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == org.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Clé API introuvable")

    api_key.is_active = False
    api_key.revoked_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info("api_key_revoked", key_id=str(key_id), org_id=str(org.id))

    return {"status": "revoked", "key_id": str(key_id)}
