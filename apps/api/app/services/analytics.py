"""Service d'analytics — statistiques organisationnelles et activité."""
import uuid
import structlog
from datetime import datetime, timezone, timedelta
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, text

from app.models.project import AoProject
from app.models.document import AoDocument

logger = structlog.get_logger(__name__)


async def get_org_stats(db: AsyncSession, org_id: uuid.UUID) -> dict:
    """
    Calcule les statistiques globales de l'organisation.

    Retourne :
        - total_projects : nombre total de projets
        - projects_by_status : répartition par statut
        - total_documents : nombre total de documents
        - avg_docs_per_project : moyenne de documents par projet
        - projects_this_month : projets créés le mois en cours
        - most_common_doc_types : types de documents les plus fréquents
        - avg_analysis_time_minutes : durée moyenne d'analyse (updated_at - created_at)
    """
    now = datetime.now(timezone.utc)

    # ── Total projets ──────────────────────────────────────────────────
    total_projects_result = await db.execute(
        select(func.count(AoProject.id)).where(AoProject.org_id == org_id)
    )
    total_projects: int = total_projects_result.scalar_one() or 0

    # ── Projets par statut ─────────────────────────────────────────────
    status_result = await db.execute(
        select(AoProject.status, func.count(AoProject.id))
        .where(AoProject.org_id == org_id)
        .group_by(AoProject.status)
    )
    projects_by_status: dict[str, int] = {
        row[0]: row[1] for row in status_result.all()
    }
    # S'assurer que tous les statuts sont présents
    for status in ("draft", "analyzing", "ready", "archived"):
        projects_by_status.setdefault(status, 0)

    # ── Total documents ────────────────────────────────────────────────
    total_docs_result = await db.execute(
        select(func.count(AoDocument.id))
        .join(AoProject, AoDocument.project_id == AoProject.id)
        .where(AoProject.org_id == org_id)
    )
    total_documents: int = total_docs_result.scalar_one() or 0

    # ── Moyenne docs/projet ────────────────────────────────────────────
    avg_docs_per_project: float = (
        round(total_documents / total_projects, 2) if total_projects > 0 else 0.0
    )

    # ── Projets ce mois ────────────────────────────────────────────────
    projects_this_month_result = await db.execute(
        select(func.count(AoProject.id)).where(
            AoProject.org_id == org_id,
            extract("year", AoProject.created_at) == now.year,
            extract("month", AoProject.created_at) == now.month,
        )
    )
    projects_this_month: int = projects_this_month_result.scalar_one() or 0

    # ── Types de documents les plus fréquents ─────────────────────────
    doc_types_result = await db.execute(
        select(AoDocument.doc_type, func.count(AoDocument.id).label("cnt"))
        .join(AoProject, AoDocument.project_id == AoProject.id)
        .where(AoProject.org_id == org_id, AoDocument.doc_type.isnot(None))
        .group_by(AoDocument.doc_type)
        .order_by(text("cnt DESC"))
        .limit(5)
    )
    most_common_doc_types: list[str] = [
        row[0] for row in doc_types_result.all() if row[0]
    ]

    # ── Durée moyenne d'analyse ────────────────────────────────────────
    # Calculé sur les projets "ready" (analyse terminée)
    # durée = updated_at - created_at en minutes
    analysis_time_result = await db.execute(
        select(AoProject.created_at, AoProject.updated_at)
        .where(AoProject.org_id == org_id, AoProject.status == "ready")
    )
    analysis_rows = analysis_time_result.all()

    avg_analysis_time_minutes: float = 0.0
    if analysis_rows:
        durations = []
        for created_at, updated_at in analysis_rows:
            if created_at and updated_at and updated_at > created_at:
                delta = (updated_at - created_at).total_seconds() / 60.0
                # Filtrer les durées aberrantes (> 24h = données de test)
                if delta < 1440:
                    durations.append(delta)
        if durations:
            avg_analysis_time_minutes = round(sum(durations) / len(durations), 1)

    # ── Win/Loss stats (R4) ────────────────────────────────────────────
    win_loss_result = await db.execute(
        select(AoProject.result, func.count(AoProject.id), func.sum(AoProject.result_amount_eur))
        .where(AoProject.org_id == org_id, AoProject.result.isnot(None))
        .group_by(AoProject.result)
    )
    win_loss_rows = win_loss_result.all()

    results_by_type: dict[str, int] = {"won": 0, "lost": 0, "no_bid": 0}
    total_won_amount_eur: float = 0.0

    for result_type, count, amount_sum in win_loss_rows:
        if result_type in results_by_type:
            results_by_type[result_type] = count
        if result_type == "won" and amount_sum:
            total_won_amount_eur = round(float(amount_sum), 2)

    total_decided = results_by_type["won"] + results_by_type["lost"]
    win_rate_pct: float = (
        round((results_by_type["won"] / total_decided) * 100, 1)
        if total_decided > 0 else 0.0
    )

    return {
        "total_projects": total_projects,
        "projects_by_status": projects_by_status,
        "total_documents": total_documents,
        "avg_docs_per_project": avg_docs_per_project,
        "projects_this_month": projects_this_month,
        "most_common_doc_types": most_common_doc_types,
        "avg_analysis_time_minutes": avg_analysis_time_minutes,
        # Win/Loss
        "win_loss": results_by_type,
        "win_rate_pct": win_rate_pct,
        "total_won_amount_eur": total_won_amount_eur,
    }


async def get_org_activity(db: AsyncSession, org_id: uuid.UUID, days: int = 30) -> list[dict]:
    """
    Retourne l'activité de l'organisation sur les N derniers jours.

    Retourne une liste de dicts :
        [{"date": "YYYY-MM-DD", "projects_created": int, "documents_uploaded": int}, ...]
    Inclut tous les jours, même ceux sans activité (count = 0).
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days - 1)

    # ── Projets créés par jour ─────────────────────────────────────────
    projects_by_day_result = await db.execute(
        select(
            func.date(AoProject.created_at).label("day"),
            func.count(AoProject.id).label("cnt"),
        )
        .where(
            AoProject.org_id == org_id,
            AoProject.created_at >= start_date,
        )
        .group_by(func.date(AoProject.created_at))
    )
    projects_by_day: dict[str, int] = {
        str(row[0]): row[1] for row in projects_by_day_result.all()
    }

    # ── Documents uploadés par jour ────────────────────────────────────
    docs_by_day_result = await db.execute(
        select(
            func.date(AoDocument.uploaded_at).label("day"),
            func.count(AoDocument.id).label("cnt"),
        )
        .join(AoProject, AoDocument.project_id == AoProject.id)
        .where(
            AoProject.org_id == org_id,
            AoDocument.uploaded_at >= start_date,
        )
        .group_by(func.date(AoDocument.uploaded_at))
    )
    docs_by_day: dict[str, int] = {
        str(row[0]): row[1] for row in docs_by_day_result.all()
    }

    # ── Construire la série complète (tous les jours) ──────────────────
    activity: list[dict] = []
    for i in range(days):
        day = (start_date + timedelta(days=i)).date()
        day_str = str(day)
        activity.append({
            "date": day_str,
            "projects_created": projects_by_day.get(day_str, 0),
            "documents_uploaded": docs_by_day.get(day_str, 0),
        })

    return activity
