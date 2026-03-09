"""Routes veille AO — configuration, résultats BOAMP et synchronisation manuelle."""
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.ao_alert import AoWatchConfig, AoWatchResult
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class WatchConfigIn(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    cpv_codes: list[str] = Field(default_factory=list)
    min_budget_eur: int | None = Field(default=None, ge=0)
    max_budget_eur: int | None = Field(default=None, ge=0)
    is_active: bool = True
    ted_enabled: bool = False


class WatchConfigOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    keywords: list[str]
    regions: list[str]
    cpv_codes: list[str]
    min_budget_eur: int | None
    max_budget_eur: int | None
    is_active: bool
    ted_enabled: bool
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WatchResultOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    source: str = "BOAMP"
    boamp_ref: str
    title: str
    buyer: str | None
    region: str | None
    publication_date: datetime | None
    deadline_date: datetime | None
    estimated_value_eur: int | None
    procedure: str | None
    cpv_codes: list[str]
    url: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchResultListOut(BaseModel):
    items: list[WatchResultOut]
    total: int
    unread_count: int


class SyncOut(BaseModel):
    task_id: str | None
    new_results: int
    message: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/config", response_model=WatchConfigOut | None)
async def get_watch_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Récupère la configuration de veille de l'organisation."""
    result = await db.execute(
        select(AoWatchConfig).where(AoWatchConfig.org_id == org.id)
    )
    config = result.scalar_one_or_none()
    return config


@router.put("/config", response_model=WatchConfigOut)
async def upsert_watch_config(
    data: WatchConfigIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée ou met à jour la configuration de veille de l'organisation."""
    result = await db.execute(
        select(AoWatchConfig).where(AoWatchConfig.org_id == org.id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        config = AoWatchConfig(
            org_id=org.id,
            **data.model_dump(),
        )
        db.add(config)
    else:
        for field, value in data.model_dump().items():
            setattr(config, field, value)
        config.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(config)
    return config


@router.get("/results", response_model=WatchResultListOut)
async def list_watch_results(
    is_read: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Liste les AO récupérés par la veille, avec filtre optionnel sur is_read."""
    base_q = select(AoWatchResult).where(AoWatchResult.org_id == org.id)

    if is_read is not None:
        base_q = base_q.where(AoWatchResult.is_read == is_read)

    # Tri : non lus en premier, puis par date de publication desc
    q = (
        base_q
        .order_by(AoWatchResult.is_read.asc(), AoWatchResult.publication_date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    items = result.scalars().all()

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(AoWatchResult).where(AoWatchResult.org_id == org.id)
    )
    total = count_result.scalar_one()

    # Count non lus
    unread_result = await db.execute(
        select(func.count())
        .select_from(AoWatchResult)
        .where(AoWatchResult.org_id == org.id, AoWatchResult.is_read.is_(False))
    )
    unread_count = unread_result.scalar_one()

    return WatchResultListOut(items=list(items), total=total, unread_count=unread_count)


@router.post("/results/{result_id}/read", response_model=WatchResultOut)
async def mark_result_read(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Marque un résultat de veille comme lu."""
    result = await db.execute(
        select(AoWatchResult).where(
            AoWatchResult.id == result_id,
            AoWatchResult.org_id == org.id,
        )
    )
    watch_result = result.scalar_one_or_none()
    if not watch_result:
        raise HTTPException(status_code=404, detail="Résultat introuvable")

    watch_result.is_read = True
    await db.flush()
    await db.refresh(watch_result)
    return watch_result


@router.post("/sync", response_model=SyncOut)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Déclenche une synchronisation manuelle des AO BOAMP pour l'organisation.

    La synchronisation s'effectue en tâche Celery pour ne pas bloquer la requête.
    """
    # Vérifier qu'une config existe
    config_result = await db.execute(
        select(AoWatchConfig).where(AoWatchConfig.org_id == org.id)
    )
    config = config_result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=400,
            detail="Aucune configuration de veille. Configurez d'abord vos critères.",
        )

    if not config.is_active:
        raise HTTPException(
            status_code=400,
            detail="La veille est désactivée. Activez-la dans la configuration.",
        )

    # Envoyer la tâche Celery de sync pour cette org uniquement
    try:
        from app.worker.tasks import sync_boamp_all_orgs
        # On utilise apply_async avec un filtre org pour déclencher uniquement cet org
        # La task sync_boamp_all_orgs parcourt toutes les orgs actives ; pour un sync
        # ciblé on utilise une variante inline via background_tasks
        org_id_str = str(org.id)
        background_tasks.add_task(_sync_org_background, org_id_str)
        return SyncOut(
            task_id=None,
            new_results=0,
            message="Synchronisation lancée en arrière-plan. Rafraîchissez dans quelques secondes.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur déclenchement sync : {exc}")


async def _sync_org_background(org_id_str: str) -> None:
    """Tâche background FastAPI : sync BOAMP + TED (si activé) pour un seul org."""
    import asyncio
    import uuid as uuid_lib
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select as sa_select
    from app.config import settings
    from app.services.boamp_watcher import sync_watch_results
    from app.services.ted_service import search_ted_notices

    org_uuid = uuid_lib.UUID(org_id_str)

    SyncEngine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    SyncSessionLocal = sessionmaker(bind=SyncEngine)
    db = SyncSessionLocal()
    try:
        # 1. Sync BOAMP (synchrone)
        sync_watch_results(db, org_uuid)

        # 2. Sync TED si activé pour cette org
        config = (
            db.query(AoWatchConfig)
            .filter(AoWatchConfig.org_id == org_uuid, AoWatchConfig.is_active.is_(True))
            .first()
        )
        if config and getattr(config, "ted_enabled", False):
            # Pays cibles : France + Belgique + Luxembourg (couverture Wallonie)
            ted_countries = ["FR", "BE", "LU"]
            ted_results = asyncio.run(
                search_ted_notices(
                    keywords=config.keywords or [],
                    cpv_codes=config.cpv_codes or [],
                    countries=ted_countries,
                    days_back=7,
                )
            )

            # Charger les refs TED déjà connues pour éviter les doublons
            existing_refs: set[str] = {
                row[0]
                for row in db.query(AoWatchResult.boamp_ref)
                .filter(AoWatchResult.org_id == org_uuid)
                .all()
            }

            for item in ted_results:
                boamp_ref = item.get("boamp_ref", "")
                if not boamp_ref or boamp_ref in existing_refs:
                    continue
                watch_result = AoWatchResult(
                    org_id=org_uuid,
                    source="TED",
                    boamp_ref=boamp_ref,
                    title=item.get("title", "")[:1000],
                    buyer=item.get("buyer"),
                    region=item.get("region"),
                    publication_date=item.get("publication_date"),
                    deadline_date=item.get("deadline_date"),
                    estimated_value_eur=item.get("estimated_value_eur"),
                    procedure=item.get("procedure"),
                    cpv_codes=item.get("cpv_codes", []),
                    url=item.get("url"),
                    is_read=False,
                )
                db.add(watch_result)
                existing_refs.add(boamp_ref)

            db.commit()

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Background sync org=%s failed: %s", org_id_str, exc)
    finally:
        db.close()
        SyncEngine.dispose()
