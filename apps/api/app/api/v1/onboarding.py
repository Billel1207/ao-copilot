from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class OnboardingStep1(BaseModel):
    company_name: Optional[str] = None
    siret: Optional[str] = None
    sector: Optional[str] = None  # gros_oeuvre|second_oeuvre|vrd|ingenierie|autre
    regions: Optional[list[str]] = None  # e.g. ["Île-de-France", "Normandie"]


class OnboardingStep2(BaseModel):
    doc_types: Optional[list[str]] = None  # RC|CCTP|CCAP|DPGF|BPU
    notify_analysis: Optional[bool] = True
    notify_deadline: Optional[bool] = True
    notify_quota: Optional[bool] = True


class OnboardingCompleteRequest(BaseModel):
    step1: Optional[OnboardingStep1] = None
    step2: Optional[OnboardingStep2] = None


@router.post("/complete")
async def complete_onboarding(
    data: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    if org:
        org.onboarding_completed = True

    # Optionnel: sauvegarder le profil entreprise si CompanyProfile existe et step1 fourni
    if data.step1 and org:
        try:
            from app.models.company_profile import CompanyProfile
            cp_result = await db.execute(select(CompanyProfile).where(CompanyProfile.org_id == org.id))
            cp = cp_result.scalar_one_or_none()
            if not cp:
                cp = CompanyProfile(org_id=org.id)
                db.add(cp)
            if data.step1.siret:
                cp.siret = data.step1.siret
            if data.step1.sector:
                cp.sector = data.step1.sector
        except Exception:
            pass  # CompanyProfile optionnel

    await db.commit()
    return {"ok": True}


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    return {"onboarding_completed": org.onboarding_completed if org else True}
