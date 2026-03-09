"""Routes d'analytics — statistiques organisationnelles et activité sur 30 jours."""
import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org
from app.services.analytics import get_org_stats, get_org_activity

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
) -> dict:
    """
    Retourne les statistiques globales de l'organisation courante.

    Inclut : total projets, répartition par statut, total documents,
    moyenne docs/projet, projets ce mois, types de docs fréquents,
    durée moyenne d'analyse.
    """
    result = await get_org_stats(db=db, org_id=org.id)
    logger.info("analytics_stats_fetched", org_id=str(org.id), user_id=str(current_user.id))
    return result


@router.get("/activity")
async def activity(
    days: int = Query(default=30, ge=7, le=90, description="Nombre de jours d'historique (7-90)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
) -> dict:
    """
    Retourne l'activité de l'organisation sur les N derniers jours.

    Chaque entrée contient la date, le nombre de projets créés et de documents uploadés.
    Tous les jours sont inclus, même ceux sans activité.
    """
    series = await get_org_activity(db=db, org_id=org.id, days=days)
    logger.info("analytics_activity_fetched", org_id=str(org.id), days=days)
    return {
        "org_id": str(org.id),
        "days": days,
        "series": series,
    }
