import uuid
from datetime import datetime, timezone
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from icalendar import Calendar, Event as ICalEvent

from app.database import get_db
from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.deadline import ProjectDeadline
from app.models.user import User
from app.models.organization import Organization
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectListOut
from app.api.v1.deps import get_current_user, get_current_org
from app.services.audit import log_action_async

router = APIRouter()

# Statuts Kanban dans l'ordre d'affichage
PIPELINE_STATUSES = ["draft", "processing", "analyzing", "ready", "archived"]

# ── Templates projets prédéfinis (R5) ───────────────────────────────────────
PROJECT_TEMPLATES = [
    {
        "id": "maitrise_oeuvre",
        "name": "Maîtrise d'œuvre",
        "icon": "🏛️",
        "description": "Missions MOE architecture et ingénierie",
        "market_type": "services",
        "doc_types_expected": ["RC", "CCTP", "AE", "ATTRI"],
    },
    {
        "id": "gros_oeuvre",
        "name": "Gros œuvre / Structure",
        "icon": "🏗️",
        "description": "Béton armé, charpente, fondations",
        "market_type": "travaux",
        "doc_types_expected": ["RC", "CCTP", "CCAP", "DPGF", "BPU"],
    },
    {
        "id": "vrd",
        "name": "VRD / Voirie Réseaux",
        "icon": "🛣️",
        "description": "Voirie, réseaux divers, terrassements",
        "market_type": "travaux",
        "doc_types_expected": ["RC", "CCTP", "CCAP", "DPGF"],
    },
    {
        "id": "electricite_cvc",
        "name": "Électricité / CVC",
        "icon": "⚡",
        "description": "Lots électricité, chauffage, ventilation",
        "market_type": "travaux",
        "doc_types_expected": ["RC", "CCTP", "CCAP", "BPU", "DPGF"],
    },
    {
        "id": "nettoyage",
        "name": "Nettoyage / Propreté",
        "icon": "🧹",
        "description": "Services d'entretien et nettoyage",
        "market_type": "services",
        "doc_types_expected": ["RC", "CCTP", "AE"],
    },
]


# ── Schéma Win/Loss update ───────────────────────────────────────────────────
class ProjectResultUpdate(BaseModel):
    result: Literal["won", "lost", "no_bid"]
    result_amount_eur: float | None = None
    result_date: datetime | None = None
    result_notes: str | None = Field(None, max_length=500)


@router.get("/pipeline/stats")
async def get_pipeline_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
) -> dict[str, Any]:
    """Retourne les projets groupés par statut (vue Kanban) + statistiques globales."""

    # Récupère tous les projets de l'org avec le comptage de documents via sous-requête
    docs_count_subq = (
        select(AoDocument.project_id, func.count(AoDocument.id).label("docs_count"))
        .group_by(AoDocument.project_id)
        .subquery()
    )

    projects_result = await db.execute(
        select(
            AoProject.id,
            AoProject.title,
            AoProject.buyer,
            AoProject.status,
            AoProject.submission_deadline,
            AoProject.reference,
            func.coalesce(docs_count_subq.c.docs_count, 0).label("docs_count"),
        )
        .outerjoin(docs_count_subq, AoProject.id == docs_count_subq.c.project_id)
        .where(AoProject.org_id == org.id)
        .order_by(AoProject.updated_at.desc())
    )
    rows = projects_result.all()

    # Groupe les projets par statut Kanban
    columns: dict[str, list[dict]] = {s: [] for s in PIPELINE_STATUSES}
    total_projects = len(rows)
    total_won = 0  # "ready" est assimilé à "gagné" pour le taux de réussite

    for row in rows:
        project_status = row.status if row.status in PIPELINE_STATUSES else "draft"
        if project_status == "ready":
            total_won += 1

        deadline_str: str | None = None
        if row.submission_deadline:
            deadline_str = row.submission_deadline.strftime("%Y-%m-%dT%H:%M:%SZ")

        columns[project_status].append({
            "id": str(row.id),
            "title": row.title,
            "buyer": row.buyer,
            "submission_deadline": deadline_str,
            "docs_count": row.docs_count,
            "reference": row.reference,
        })

    win_rate_pct = round((total_won / total_projects) * 100) if total_projects > 0 else 0

    return {
        "columns": columns,
        "stats": {
            "total_projects": total_projects,
            "total_won": total_won,
            "win_rate_pct": win_rate_pct,
            "avg_market_size_eur": None,  # Réservé pour une future fonctionnalité
        },
    }


@router.get("/templates")
async def get_project_templates(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Retourne la liste des templates de projets prédéfinis (R5)."""
    return PROJECT_TEMPLATES


@router.get("", response_model=ProjectListOut)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    query = select(AoProject).where(AoProject.org_id == org.id)
    if status_filter:
        query = query.where(AoProject.status == status_filter)
    if q and q.strip():
        query = query.where(
            or_(
                AoProject.title.ilike(f"%{q.strip()}%"),
                AoProject.buyer.ilike(f"%{q.strip()}%"),
                AoProject.reference.ilike(f"%{q.strip()}%"),
            )
        )
    query = query.order_by(AoProject.updated_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    projects = result.scalars().all()

    count_q = select(func.count()).select_from(AoProject).where(AoProject.org_id == org.id)
    if q and q.strip():
        count_q = count_q.where(
            or_(
                AoProject.title.ilike(f"%{q.strip()}%"),
                AoProject.buyer.ilike(f"%{q.strip()}%"),
                AoProject.reference.ilike(f"%{q.strip()}%"),
            )
        )
    count_result = await db.execute(count_q)
    total = count_result.scalar_one()

    return ProjectListOut(items=list(projects), total=total)


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    project = AoProject(
        org_id=org.id,
        created_by=current_user.id,
        **data.model_dump(exclude_none=True),
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    log_action_async(
        db, action="project.create",
        user_id=str(current_user.id), org_id=str(org.id),
        resource_type="project", resource_id=str(project.id),
        extra={"title": project.title},
    )

    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def archive_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project.status = "archived"
    project.updated_at = datetime.now(timezone.utc)
    await db.flush()

    log_action_async(
        db, action="project.archive",
        user_id=str(current_user.id), org_id=str(org.id),
        resource_type="project", resource_id=str(project_id),
        extra={"title": project.title},
    )
    # Le context manager get_db() gère le commit — pas de double commit


@router.patch("/{project_id}/result", response_model=ProjectOut)
async def update_project_result(
    project_id: uuid.UUID,
    data: ProjectResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Enregistre le résultat d'un appel d'offres : won | lost | no_bid (R4)."""
    result_q = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result_q.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project.result = data.result
    project.result_amount_eur = data.result_amount_eur
    project.result_date = data.result_date or datetime.now(timezone.utc)
    project.result_notes = data.result_notes
    project.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(project)

    log_action_async(
        db, action="project.result_updated",
        user_id=str(current_user.id), org_id=str(org.id),
        resource_type="project", resource_id=str(project_id),
        extra={"result": data.result, "amount_eur": data.result_amount_eur},
    )

    return project


@router.get("/{project_id}/deadlines/ical")
async def export_deadlines_ical(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Exporte les dates clés d'un projet au format iCalendar (.ics)."""
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    deadlines_result = await db.execute(
        select(ProjectDeadline).where(ProjectDeadline.project_id == project_id)
    )
    deadlines = deadlines_result.scalars().all()

    cal = Calendar()
    cal.add("prodid", "-//AO Copilot//DCE Intelligence//FR")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", f"AO - {project.title}")

    for d in deadlines:
        event = ICalEvent()
        event.add("summary", f"[AO] {d.label}")
        deadline_date = d.deadline_date.date() if d.deadline_date else datetime.now(timezone.utc).date()
        event.add("dtstart", deadline_date)
        event.add("dtend", deadline_date)
        event.add("description", f"Projet: {project.title}\nType: {d.deadline_type}")
        cal.add_component(event)

    return FastAPIResponse(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=deadlines_{project_id}.ics"},
    )
