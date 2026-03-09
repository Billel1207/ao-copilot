"""Routes e-Attestations — vérification de conformité réglementaire."""
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.eattestation_service import verify_company_attestations
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/company")
async def get_company_attestations(
    siret: str = Query(..., description="SIRET de l'entreprise à vérifier (9 à 14 chiffres)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Vérifie les attestations de conformité d'une entreprise via son SIRET.
    Utilise l'API e-Attestations.com (ou données simulées si clé absente).
    """
    try:
        results = await verify_company_attestations(siret)
        return {
            "siret": siret.replace(" ", ""),
            "checked_at": dt.datetime.utcnow().isoformat(),
            "attestations": results,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/my-company")
async def get_my_company_attestations(
    siret: str = Query(..., description="SIRET de votre entreprise (9 à 14 chiffres)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Vérifie les attestations de l'entreprise du user connecté.
    Requiert le SIRET en paramètre (renseignez-le depuis votre profil entreprise).
    """
    try:
        attestations = await verify_company_attestations(siret)
        return {
            "siret": siret.replace(" ", ""),
            "checked_at": dt.datetime.utcnow().isoformat(),
            "attestations": attestations,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
