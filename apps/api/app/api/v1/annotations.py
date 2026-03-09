"""Routes d'annotations collaboratives sur les items de checklist."""
import uuid
from datetime import datetime
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.analysis import ChecklistItem
from app.models.annotation import ChecklistAnnotation
from app.models.project import AoProject
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AnnotationCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    annotation_type: Literal["comment", "question", "validated", "flag"] = "comment"


class AnnotationResponse(BaseModel):
    id: str
    checklist_item_id: str
    project_id: str
    user_id: str
    content: str
    annotation_type: str
    author_name: str | None
    author_email: str | None
    created_at: datetime
    updated_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project_and_item(
    project_id: str,
    item_id: str,
    current_user: User,
    db: Session,
) -> tuple[AoProject, ChecklistItem]:
    try:
        proj_uuid = uuid.UUID(project_id)
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID invalide")

    project = db.query(AoProject).filter_by(id=proj_uuid, org_id=current_user.org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    item = db.query(ChecklistItem).filter_by(id=item_uuid, project_id=proj_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist introuvable")

    return project, item


def _to_response(a: ChecklistAnnotation) -> AnnotationResponse:
    return AnnotationResponse(
        id=str(a.id),
        checklist_item_id=str(a.checklist_item_id),
        project_id=str(a.project_id),
        user_id=str(a.user_id),
        content=a.content,
        annotation_type=a.annotation_type,
        author_name=a.author_name,
        author_email=a.author_email,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


# ── GET /projects/{project_id}/checklist/{item_id}/annotations ───────────────

@router.get(
    "/{project_id}/checklist/{item_id}/annotations",
    response_model=list[AnnotationResponse],
)
def list_annotations(
    project_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les annotations d'un item de checklist."""
    _get_project_and_item(project_id, item_id, current_user, db)

    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="item_id invalide")

    annotations = (
        db.query(ChecklistAnnotation)
        .filter_by(checklist_item_id=item_uuid)
        .order_by(ChecklistAnnotation.created_at.asc())
        .all()
    )
    return [_to_response(a) for a in annotations]


# ── POST /projects/{project_id}/checklist/{item_id}/annotations ──────────────

@router.post(
    "/{project_id}/checklist/{item_id}/annotations",
    response_model=AnnotationResponse,
    status_code=201,
)
def create_annotation(
    project_id: str,
    item_id: str,
    body: AnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crée une annotation sur un item de checklist."""
    project, item = _get_project_and_item(project_id, item_id, current_user, db)

    annotation = ChecklistAnnotation(
        checklist_item_id=item.id,
        project_id=project.id,
        org_id=current_user.org_id,
        user_id=current_user.id,
        content=body.content.strip(),
        annotation_type=body.annotation_type,
        author_name=current_user.full_name,
        author_email=current_user.email,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)

    logger.info(
        "annotation_created",
        annotation_id=str(annotation.id),
        item_id=item_id,
        project_id=project_id,
        type=body.annotation_type,
    )
    return _to_response(annotation)


# ── DELETE /projects/{project_id}/checklist/{item_id}/annotations/{annotation_id} ─

@router.delete(
    "/{project_id}/checklist/{item_id}/annotations/{annotation_id}",
    status_code=204,
)
def delete_annotation(
    project_id: str,
    item_id: str,
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Supprime une annotation (auteur ou admin/owner seulement)."""
    _get_project_and_item(project_id, item_id, current_user, db)

    try:
        ann_uuid = uuid.UUID(annotation_id)
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID invalide")

    annotation = db.query(ChecklistAnnotation).filter_by(
        id=ann_uuid, checklist_item_id=item_uuid
    ).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation introuvable")

    # Seuls l'auteur ou un admin/owner peuvent supprimer
    is_author = annotation.user_id == current_user.id
    is_admin = current_user.role in ("admin", "owner")
    if not is_author and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres annotations",
        )

    db.delete(annotation)
    db.commit()
    logger.info("annotation_deleted", annotation_id=annotation_id, user_id=str(current_user.id))
    return None
