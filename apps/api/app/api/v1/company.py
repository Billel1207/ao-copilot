"""Routes API pour le profil entreprise — GET/PUT /company/profile."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CompanyProfileIn(BaseModel):
    revenue_eur: int | None = Field(None, ge=0, description="CA annuel en euros")
    employee_count: int | None = Field(None, ge=0, description="Nombre de salariés")
    certifications: list[str] = Field(
        default_factory=list,
        description="Certifications : Qualibat, ISO9001, MASE, RGE, OPQIBI, etc."
    )
    specialties: list[str] = Field(
        default_factory=list,
        description="Domaines d'activité BTP"
    )
    regions: list[str] = Field(
        default_factory=list,
        description="Régions d'intervention"
    )
    max_market_size_eur: int | None = Field(
        None, ge=0, description="Taille maximale du marché gérable en euros"
    )


class CompanyProfileOut(BaseModel):
    id: str
    org_id: str
    revenue_eur: int | None
    employee_count: int | None
    certifications: list[str]
    specialties: list[str]
    regions: list[str]
    max_market_size_eur: int | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/profile", response_model=CompanyProfileOut)
async def get_company_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Retourne le profil entreprise de l'organisation courante."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.org_id == org.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profil entreprise non configuré — utilisez PUT /company/profile pour le créer"
        )

    return CompanyProfileOut(
        id=str(profile.id),
        org_id=str(profile.org_id),
        revenue_eur=profile.revenue_eur,
        employee_count=profile.employee_count,
        certifications=profile.certifications or [],
        specialties=profile.specialties or [],
        regions=profile.regions or [],
        max_market_size_eur=profile.max_market_size_eur,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.put("/profile", response_model=CompanyProfileOut)
async def upsert_company_profile(
    body: CompanyProfileIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Crée ou met à jour le profil entreprise de l'organisation courante."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.org_id == org.id)
    )
    profile = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if profile:
        # Mise à jour des champs
        profile.revenue_eur = body.revenue_eur
        profile.employee_count = body.employee_count
        profile.certifications = body.certifications
        profile.specialties = body.specialties
        profile.regions = body.regions
        profile.max_market_size_eur = body.max_market_size_eur
        profile.updated_at = now
        logger.info(f"Profil entreprise mis à jour pour org={org.id}")
    else:
        profile = CompanyProfile(
            org_id=org.id,
            revenue_eur=body.revenue_eur,
            employee_count=body.employee_count,
            certifications=body.certifications,
            specialties=body.specialties,
            regions=body.regions,
            max_market_size_eur=body.max_market_size_eur,
        )
        db.add(profile)
        logger.info(f"Profil entreprise créé pour org={org.id}")

    await db.flush()
    await db.refresh(profile)

    return CompanyProfileOut(
        id=str(profile.id),
        org_id=str(profile.org_id),
        revenue_eur=profile.revenue_eur,
        employee_count=profile.employee_count,
        certifications=profile.certifications or [],
        specialties=profile.specialties or [],
        regions=profile.regions or [],
        max_market_size_eur=profile.max_market_size_eur,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )
