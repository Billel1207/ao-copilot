import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io

from app.database import get_db
from app.models.project import AoProject
from app.models.document import AoDocument
from app.models.user import User
from app.models.organization import Organization
from app.api.v1.deps import get_current_user, get_current_org

router = APIRouter()


@router.post("/{project_id}/export/pdf")
async def export_pdf(
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

    if project.status != "ready":
        raise HTTPException(status_code=400, detail="Analyse non terminée — attendez que le statut soit 'ready'")

    from app.worker.tasks import export_project_pdf
    task = export_project_pdf.delay(str(project_id))

    return {"job_id": task.id, "status": "pending"}


@router.post("/{project_id}/export/word")
async def export_word(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Export Word — plan Pro ou supérieur requis."""
    # Vérification plan Pro
    if org.plan not in ("pro", "europe", "business", "trial"):
        raise HTTPException(
            status_code=403,
            detail="L'export Word est disponible à partir du plan Pro. Mettez à niveau votre abonnement sur /billing.",
        )

    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.status != "ready":
        raise HTTPException(status_code=400, detail="Analyse non terminée — attendez que le statut soit 'ready'")

    from app.worker.tasks import export_project_docx
    task = export_project_docx.delay(str(project_id))

    return {"job_id": task.id, "status": "pending"}


@router.post("/{project_id}/export/dpgf-excel")
async def export_dpgf_excel(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Export DPGF/BPU en Excel structuré — plan Pro ou supérieur requis.

    Cherche les documents DPGF ou BPU du projet, extrait leurs tableaux
    via pdfplumber et retourne directement un fichier .xlsx en téléchargement.
    """
    # Vérification plan Pro (même gate que l'export Word)
    if org.plan not in ("pro", "europe", "business", "trial"):
        raise HTTPException(
            status_code=403,
            detail=(
                "L'export DPGF Excel est disponible à partir du plan Pro. "
                "Mettez à niveau votre abonnement sur /billing."
            ),
        )

    # Vérifier que le projet appartient bien à l'organisation
    project_result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Analyse non terminée — attendez que le statut soit 'ready'",
        )

    # Récupérer les documents DPGF ou BPU du projet
    docs_result = await db.execute(
        select(AoDocument).where(
            AoDocument.project_id == project_id,
            AoDocument.doc_type.in_(["DPGF", "BPU"]),
            AoDocument.status == "done",
        )
    )
    dpgf_docs = docs_result.scalars().all()

    if not dpgf_docs:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun document DPGF ou BPU trouvé dans ce projet. "
                "Vérifiez que les documents ont été correctement classifiés."
            ),
        )

    from app.services.storage import storage_service
    from app.services.dpgf_extractor import extract_tables_from_pdf, generate_excel
    import logging

    _log = logging.getLogger(__name__)

    all_tables = []
    for doc in dpgf_docs:
        try:
            pdf_bytes = storage_service.download_bytes(doc.s3_key)
            tables = extract_tables_from_pdf(pdf_bytes, filename=doc.original_name)
            all_tables.extend(tables)
        except Exception as exc:
            _log.warning(
                "export_dpgf_excel.doc_extraction_failed",
                doc_id=str(doc.id),
                filename=doc.original_name,
                error=str(exc),
            )
            # On continue avec les autres documents — un seul doc défaillant
            # ne doit pas bloquer l'export global

    excel_bytes = generate_excel(all_tables, project_title=project.title)

    # Nom du fichier : sanitize le titre du projet
    import re
    safe_title = re.sub(r"[^\w\-]", "_", project.title)[:50]
    filename_xlsx = f"DPGF_{safe_title}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_xlsx}"',
            "Content-Length": str(len(excel_bytes)),
        },
    )


@router.post("/{project_id}/export/memo")
async def export_memo_technique(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Génère et retourne directement une mémoire technique Word (.docx) pré-remplie par l'IA.
    Réservé au plan Pro ou supérieur.
    """
    # Vérification plan Pro (même gate que Word export)
    if org.plan not in ("pro", "europe", "business", "trial"):
        raise HTTPException(
            status_code=403,
            detail=(
                "La mémoire technique est disponible à partir du plan Pro. "
                "Mettez à niveau votre abonnement sur /billing."
            ),
        )

    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Analyse non terminée — attendez que le statut soit 'ready'",
        )

    # Dispatch vers Celery (LLM calls + charts + document = trop long pour un request sync)
    from app.worker.tasks import export_project_memo
    task = export_project_memo.delay(str(project_id))

    return {"job_id": task.id, "status": "pending"}


@router.post("/{project_id}/export/pack")
async def export_pack(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Export complet ZIP (PDF + Word + DPGF Excel + Mémoire technique). Plan Pro requis."""
    if org.plan not in ("pro", "europe", "business", "trial"):
        raise HTTPException(
            status_code=403,
            detail="L'export Pack complet est disponible à partir du plan Pro.",
        )

    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    if project.status != "ready":
        raise HTTPException(status_code=400, detail="Analyse non terminée")

    from app.worker.tasks import export_project_pack
    task = export_project_pack.delay(str(project_id))

    return {"job_id": task.id, "status": "pending"}


@router.get("/{project_id}/export/{job_id}")
async def get_export_status(
    project_id: uuid.UUID,
    job_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    from app.worker.celery_app import celery_app
    from app.services.storage import storage_service

    task = celery_app.AsyncResult(job_id)

    if task.state == "PENDING":
        return {"status": "pending", "progress": 0}
    elif task.state == "STARTED":
        return {"status": "processing", "progress": 50}
    elif task.state == "SUCCESS":
        s3_key = task.result
        signed_url = storage_service.get_signed_download_url(s3_key)
        return {"status": "done", "url": signed_url, "expires_in": 900}
    elif task.state == "FAILURE":
        return {"status": "error", "error": str(task.info)}
    else:
        return {"status": task.state.lower()}
