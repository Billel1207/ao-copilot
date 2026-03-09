import uuid
import structlog
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

logger = structlog.get_logger(__name__)

# Magic bytes par extension pour validation sécurisée
ALLOWED_EXTENSIONS: dict[str, tuple[bytes, str]] = {
    ".pdf":  (b"%PDF",        "application/pdf"),
    ".jpg":  (b"\xFF\xD8",    "image/jpeg"),
    ".jpeg": (b"\xFF\xD8",    "image/jpeg"),
    ".png":  (b"\x89PNG",     "image/png"),
    ".tiff": (b"II*\x00",     "image/tiff"),   # little-endian TIFF
    ".tif":  (b"II*\x00",     "image/tiff"),
    ".docx": (b"PK\x03\x04",  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
}

from app.database import get_db
from app.models.document import AoDocument
from app.models.project import AoProject
from app.models.user import User
from app.models.organization import Organization
from app.schemas.document import DocumentOut, SignedUrlOut
from app.api.v1.deps import get_current_user, get_current_org
from app.services.storage import storage_service
from app.core.limiter import limiter
from app.services.audit import log_action_async

router = APIRouter()

DOC_TYPE_KEYWORDS = {
    "RC": ["règlement de consultation", "reglement de consultation"],
    "CCTP": ["cahier des clauses techniques", "cctp"],
    "CCAP": ["cahier des clauses administratives particulières", "ccap"],
    "DPGF": ["décomposition du prix global", "dpgf"],
    "BPU": ["bordereau des prix unitaires", "bpu"],
    "AE": ["acte d'engagement", "acte engagement"],
    "ATTRI": ["attribution", "lettre attribution"],
}


def detect_doc_type(filename: str) -> str:
    name_lower = filename.lower()
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return doc_type
    return "AUTRES"


async def _get_project_or_404(project_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> AoProject:
    result = await db.execute(
        select(AoProject).where(AoProject.id == project_id, AoProject.org_id == org_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


@router.get("/{project_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(AoDocument).where(AoDocument.project_id == project_id).order_by(AoDocument.uploaded_at)
    )
    return list(result.scalars().all())


@router.post("/{project_id}/documents/upload", response_model=DocumentOut, status_code=201)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)

    # M2 — Quota enforcement : compter les docs uploadés ce mois pour cette org
    now = datetime.now()
    doc_count_result = await db.execute(
        select(func.count(AoDocument.id))
        .join(AoProject, AoDocument.project_id == AoProject.id)
        .where(
            AoProject.org_id == org.id,
            extract("year", AoDocument.uploaded_at) == now.year,
            extract("month", AoDocument.uploaded_at) == now.month,
        )
    )
    used_this_month = doc_count_result.scalar_one()
    if used_this_month >= org.quota_docs:
        raise HTTPException(
            status_code=429,
            detail=f"Quota mensuel atteint ({org.quota_docs} documents). Passez au plan supérieur.",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    import os
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Formats acceptés : PDF, JPEG, PNG, TIFF, DOCX"
        )

    content = await file.read()

    # Vérification magic bytes — protège contre les fichiers renommés
    magic, content_type = ALLOWED_EXTENSIONS[ext]
    if not content.startswith(magic):
        raise HTTPException(status_code=400, detail=f"Le fichier ne correspond pas au format {ext.lstrip('.')}")

    size_kb = len(content) // 1024
    if len(content) > 51200 * 1024:  # 50 Mo exact
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 50 Mo)")

    s3_key = storage_service.generate_s3_key(str(org.id), str(project_id), file.filename)
    try:
        storage_service.upload_bytes(s3_key, content, content_type)
    except Exception as exc:
        logger.error("s3_upload_failed", s3_key=s3_key, error=str(exc))
        raise HTTPException(
            status_code=503,
            detail="Service de stockage indisponible. Réessayez dans quelques instants.",
        ) from exc

    doc_type = detect_doc_type(file.filename)

    doc = AoDocument(
        project_id=project_id,
        original_name=file.filename,
        s3_key=s3_key,
        doc_type=doc_type,
        file_size_kb=size_kb,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Lancer l'extraction en background via Celery
    from app.worker.tasks import process_document
    process_document.delay(str(doc.id))

    # Audit RGPD — document uploadé
    log_action_async(
        db, action="document.upload",
        user_id=str(current_user.id), org_id=str(org.id),
        resource_type="document", resource_id=str(doc.id),
        ip=request.client.host if request.client else None,
        extra={"doc_name": file.filename, "doc_type": doc_type, "size_kb": size_kb},
    )

    return doc


@router.get("/{project_id}/documents/{doc_id}", response_model=DocumentOut)
async def get_document(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(AoDocument).where(AoDocument.id == doc_id, AoDocument.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return doc


@router.get("/{project_id}/documents/{doc_id}/signed-url", response_model=SignedUrlOut)
async def get_signed_url(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(AoDocument).where(AoDocument.id == doc_id, AoDocument.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    url = storage_service.get_signed_download_url(doc.s3_key)
    return SignedUrlOut(url=url, expires_in=900)


@router.delete("/{project_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    await _get_project_or_404(project_id, org.id, db)
    result = await db.execute(
        select(AoDocument).where(AoDocument.id == doc_id, AoDocument.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    # Supprimer la BD en premier pour garantir la cohérence :
    # si le rollback BD intervient, l'objet S3 n'est pas supprimé.
    s3_key_to_delete = doc.s3_key
    doc_name = doc.original_name
    await db.delete(doc)
    await db.flush()
    # Supprimer S3 après flush BD réussi
    try:
        storage_service.delete_object(s3_key_to_delete)
    except Exception as exc:
        logger.warning("s3_delete_failed_after_db_delete", s3_key=s3_key_to_delete, error=str(exc))

    # Audit RGPD — document supprimé
    log_action_async(
        db, action="document.delete",
        user_id=str(current_user.id), org_id=str(org.id),
        resource_type="document", resource_id=str(doc_id),
        extra={"doc_name": doc_name},
    )
