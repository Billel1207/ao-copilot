"""Routes API pour le profil entreprise — GET/PUT /company/profile + logo upload."""
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org
from app.core.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2 Mo


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
    # ── Champs Go/No-Go enrichi (Phase 6) ──
    assurance_rc_montant: int | None = Field(
        None, ge=0, description="Montant RC Pro en euros"
    )
    assurance_decennale: bool | None = Field(
        None, description="Possède une assurance décennale"
    )
    partenaires_specialites: list[str] = Field(
        default_factory=list,
        description="Spécialités des partenaires sous-traitants"
    )
    marge_minimale_pct: float | None = Field(
        None, ge=0, le=100, description="Marge minimale acceptable en %"
    )
    max_projets_simultanes: int | None = Field(
        None, ge=0, description="Capacité max de projets simultanés"
    )
    projets_actifs_count: int | None = Field(
        None, ge=0, description="Nombre de projets actifs actuellement"
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
    assurance_rc_montant: int | None = None
    assurance_decennale: bool | None = None
    partenaires_specialites: list[str] = []
    marge_minimale_pct: float | None = None
    max_projets_simultanes: int | None = None
    projets_actifs_count: int | None = None
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
        assurance_rc_montant=profile.assurance_rc_montant,
        assurance_decennale=profile.assurance_decennale,
        partenaires_specialites=profile.partenaires_specialites or [],
        marge_minimale_pct=profile.marge_minimale_pct,
        max_projets_simultanes=profile.max_projets_simultanes,
        projets_actifs_count=profile.projets_actifs_count,
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
        profile.assurance_rc_montant = body.assurance_rc_montant
        profile.assurance_decennale = body.assurance_decennale
        profile.partenaires_specialites = body.partenaires_specialites
        profile.marge_minimale_pct = body.marge_minimale_pct
        profile.max_projets_simultanes = body.max_projets_simultanes
        profile.projets_actifs_count = body.projets_actifs_count
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
            assurance_rc_montant=body.assurance_rc_montant,
            assurance_decennale=body.assurance_decennale,
            partenaires_specialites=body.partenaires_specialites,
            marge_minimale_pct=body.marge_minimale_pct,
            max_projets_simultanes=body.max_projets_simultanes,
            projets_actifs_count=body.projets_actifs_count,
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
        assurance_rc_montant=profile.assurance_rc_montant,
        assurance_decennale=profile.assurance_decennale,
        partenaires_specialites=profile.partenaires_specialites or [],
        marge_minimale_pct=profile.marge_minimale_pct,
        max_projets_simultanes=profile.max_projets_simultanes,
        projets_actifs_count=profile.projets_actifs_count,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


# ── Logo upload ──────────────────────────────────────────────────────────


@router.post("/logo")
@limiter.limit("10/hour")
async def upload_company_logo(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Upload le logo entreprise (PNG/JPEG/SVG/WebP, max 2 Mo).

    Le logo apparaîtra sur les exports PDF/DOCX/Mémo.
    """
    if file.content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté ({file.content_type}). "
                   f"Formats acceptés : PNG, JPEG, SVG, WebP.",
        )

    content = await file.read()
    if len(content) > MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux ({len(content) // 1024} Ko). Maximum : 2 Mo.",
        )

    from app.services.storage import storage_service

    ext_map = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg", "image/webp": "webp"}
    ext = ext_map.get(file.content_type, "png")
    s3_key = f"logos/{org.id}/logo_{uuid_lib.uuid4().hex[:8]}.{ext}"

    storage_service.upload_bytes(s3_key, content, file.content_type)

    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.org_id == org.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        if profile.logo_s3_key:
            try:
                storage_service.delete_object(profile.logo_s3_key)
            except Exception:
                pass
        profile.logo_s3_key = s3_key
        profile.updated_at = datetime.now(timezone.utc)
    else:
        profile = CompanyProfile(org_id=org.id, logo_s3_key=s3_key)
        db.add(profile)

    await db.flush()
    logger.info("company_logo_uploaded", org_id=str(org.id), s3_key=s3_key)

    return {"status": "ok", "logo_s3_key": s3_key, "size_kb": len(content) // 1024}


@router.delete("/logo")
async def delete_company_logo(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Supprime le logo entreprise."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.org_id == org.id)
    )
    profile = result.scalar_one_or_none()

    if not profile or not profile.logo_s3_key:
        raise HTTPException(status_code=404, detail="Aucun logo configuré")

    from app.services.storage import storage_service

    try:
        storage_service.delete_object(profile.logo_s3_key)
    except Exception:
        pass

    profile.logo_s3_key = None
    profile.updated_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info("company_logo_deleted", org_id=str(org.id))
    return {"status": "ok"}
