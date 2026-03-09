"""Routes de la bibliothèque de réponses réutilisables."""
import uuid
from datetime import datetime, timezone
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.library import ResponseSnippet
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter()

VALID_CATEGORIES = {"methodo", "references", "equipe", "moyens", "qualite"}


# ── Schemas ──────────────────────────────────────────────────────────────────

class SnippetCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    tags: list[str] = Field(default_factory=list)
    category: Literal["methodo", "references", "equipe", "moyens", "qualite"] | None = None


class SnippetUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content: str | None = None
    tags: list[str] | None = None
    category: Literal["methodo", "references", "equipe", "moyens", "qualite"] | None = None


class SnippetResponse(BaseModel):
    id: str
    org_id: str
    title: str
    content: str
    tags: list[str]
    category: str | None
    usage_count: int
    last_used_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_snippet_or_404(
    snippet_id: str,
    current_user: User,
    db: Session,
) -> ResponseSnippet:
    try:
        uid = uuid.UUID(snippet_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="snippet_id invalide")

    snippet = db.query(ResponseSnippet).filter_by(id=uid, org_id=current_user.org_id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet introuvable")
    return snippet


def _to_response(s: ResponseSnippet) -> SnippetResponse:
    return SnippetResponse(
        id=str(s.id),
        org_id=str(s.org_id),
        title=s.title,
        content=s.content,
        tags=s.tags or [],
        category=s.category,
        usage_count=s.usage_count,
        last_used_at=s.last_used_at,
        created_by=str(s.created_by),
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


# ── GET /library/snippets ─────────────────────────────────────────────────────

@router.get("/snippets", response_model=list[SnippetResponse])
def list_snippets(
    tag: str | None = Query(None, description="Filtrer par tag"),
    category: str | None = Query(None, description="Filtrer par catégorie"),
    search: str | None = Query(None, description="Recherche texte libre"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les snippets de l'organisation avec filtres optionnels."""
    q = db.query(ResponseSnippet).filter_by(org_id=current_user.org_id)

    if category:
        q = q.filter(ResponseSnippet.category == category)

    if search:
        like = f"%{search}%"
        q = q.filter(
            ResponseSnippet.title.ilike(like) | ResponseSnippet.content.ilike(like)
        )

    snippets = q.order_by(ResponseSnippet.usage_count.desc(), ResponseSnippet.created_at.desc()).all()

    # Filtre tag en Python (JSON array — évite la complexité SQL cross-DB)
    if tag:
        snippets = [s for s in snippets if tag in (s.tags or [])]

    return [_to_response(s) for s in snippets]


# ── POST /library/snippets ────────────────────────────────────────────────────

@router.post("/snippets", response_model=SnippetResponse, status_code=201)
def create_snippet(
    body: SnippetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crée un nouveau snippet de réponse."""
    snippet = ResponseSnippet(
        org_id=current_user.org_id,
        title=body.title.strip(),
        content=body.content,
        tags=body.tags,
        category=body.category,
        usage_count=0,
        created_by=current_user.id,
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    logger.info("snippet_created", snippet_id=str(snippet.id), org_id=str(current_user.org_id))
    return _to_response(snippet)


# ── PUT /library/snippets/{id} ────────────────────────────────────────────────

@router.put("/snippets/{snippet_id}", response_model=SnippetResponse)
def update_snippet(
    snippet_id: str,
    body: SnippetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Modifie un snippet existant."""
    snippet = _get_snippet_or_404(snippet_id, current_user, db)

    if body.title is not None:
        snippet.title = body.title.strip()
    if body.content is not None:
        snippet.content = body.content
    if body.tags is not None:
        snippet.tags = body.tags
    if body.category is not None:
        snippet.category = body.category

    snippet.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snippet)
    logger.info("snippet_updated", snippet_id=snippet_id, org_id=str(current_user.org_id))
    return _to_response(snippet)


# ── DELETE /library/snippets/{id} ────────────────────────────────────────────

@router.delete("/snippets/{snippet_id}", status_code=204)
def delete_snippet(
    snippet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Supprime un snippet."""
    snippet = _get_snippet_or_404(snippet_id, current_user, db)
    db.delete(snippet)
    db.commit()
    logger.info("snippet_deleted", snippet_id=snippet_id, org_id=str(current_user.org_id))
    return None


# ── POST /library/snippets/{id}/use ──────────────────────────────────────────

@router.post("/snippets/{snippet_id}/use", response_model=SnippetResponse)
def record_snippet_use(
    snippet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Incrémente le compteur d'utilisation et met à jour last_used_at."""
    snippet = _get_snippet_or_404(snippet_id, current_user, db)
    snippet.usage_count = (snippet.usage_count or 0) + 1
    snippet.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snippet)
    return _to_response(snippet)
