"""GDPR endpoints — droit à l'effacement, export de données, préférences email."""
import uuid
import json
import structlog
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.analysis import ExtractionResult, ChecklistItem, CriteriaItem
from app.models.company_profile import CompanyProfile
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/delete", status_code=202)
async def request_account_deletion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Demande de suppression du compte (RGPD Art. 17 — droit à l'effacement).

    Effectue un soft-delete de l'organisation et anonymise les données utilisateur.
    Les fichiers S3 seront purgés par la tâche Celery purge_expired_data.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Seul le propriétaire de l'organisation peut demander la suppression.",
        )

    now = datetime.now(timezone.utc)

    # Soft-delete l'organisation
    org.deleted_at = now

    # Anonymiser les utilisateurs de l'org
    result = await db.execute(
        select(User).where(User.org_id == org.id)
    )
    users = result.scalars().all()
    for user in users:
        user.email = f"deleted-{user.id}@anonymized.local"
        user.full_name = "Compte supprimé"
        user.hashed_pw = "DELETED"

    await db.flush()

    logger.info(
        "gdpr_account_deletion_requested",
        org_id=str(org.id),
        user_id=str(current_user.id),
        user_count=len(users),
    )

    return {
        "message": "Demande de suppression enregistrée. Vos données seront effacées sous 30 jours.",
        "org_id": str(org.id),
        "deleted_at": now.isoformat(),
    }


@router.get("/export")
async def export_user_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Export de toutes les données personnelles (RGPD Art. 20 — droit à la portabilité).

    Retourne un JSON structuré avec toutes les données de l'utilisateur et de son organisation.
    """
    # Données utilisateur
    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }

    # Données organisation
    org_data = {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "plan": org.plan,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }

    # Projets
    projects_result = await db.execute(
        select(AoProject).where(AoProject.org_id == org.id)
    )
    projects = projects_result.scalars().all()
    projects_data = [
        {
            "id": str(p.id),
            "title": p.title,
            "reference": p.reference,
            "buyer": p.buyer,
            "market_type": p.market_type,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]

    # Documents (métadonnées uniquement, pas les fichiers)
    docs_result = await db.execute(
        select(AoDocument).where(
            AoDocument.project_id.in_([p.id for p in projects])
        )
    ) if projects else None
    docs_data = []
    if docs_result:
        for d in docs_result.scalars().all():
            docs_data.append({
                "id": str(d.id),
                "project_id": str(d.project_id),
                "filename": d.original_name,
                "doc_type": d.doc_type,
                "status": d.status,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            })

    # Profil entreprise
    profile_result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.org_id == org.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_data = None
    if profile:
        profile_data = {
            "revenue_eur": profile.revenue_eur,
            "employee_count": profile.employee_count,
            "certifications": profile.certifications,
            "specialties": profile.specialties,
            "regions": profile.regions,
        }

    logger.info("gdpr_data_export", user_id=str(current_user.id), org_id=str(org.id))

    return {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "user": user_data,
        "organization": org_data,
        "projects": projects_data,
        "documents": docs_data,
        "company_profile": profile_data,
    }


@router.post("/unsubscribe-emails")
async def unsubscribe_emails(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Désabonnement des emails de notification (RGPD — consentement).

    Note : stocke la préférence dans Redis car le modèle User n'a pas
    de colonne email_preferences. Une migration future pourra l'ajouter.
    """
    import redis as redis_lib
    from app.config import settings

    try:
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        r.set(f"email_unsubscribed:{current_user.id}", "1")
    except Exception as exc:
        logger.error("gdpr_unsubscribe_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Erreur interne")

    logger.info("gdpr_email_unsubscribe", user_id=str(current_user.id))

    return {"message": "Vous avez été désabonné des emails de notification."}
