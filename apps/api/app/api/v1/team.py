"""Routes de gestion d'équipe : invitations, membres, rôles."""
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.team import TeamInvite
from app.models.user import User
from app.models.organization import Organization
from app.services.email import send_team_invite

logger = structlog.get_logger(__name__)
router = APIRouter()

INVITE_TTL_DAYS = 7


# ── Schemas ─────────────────────────────────────────────────────────────

class InviteRequest(BaseModel):
    email: EmailStr
    role: Literal["member", "admin"] = "member"


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    invited_by_name: str | None
    created_at: datetime
    expires_at: datetime
    accepted: bool


class MemberResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    created_at: datetime
    last_login_at: datetime | None


class RoleUpdateRequest(BaseModel):
    role: Literal["member", "admin"]


# ── Helpers ─────────────────────────────────────────────────────────────

def _require_admin(current_user: User):
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux administrateurs")


# ── GET /team/members ────────────────────────────────────────────────────

@router.get("/{org_slug}/members", response_model=list[MemberResponse])
def list_members(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les membres de l'organisation courante."""
    org = db.query(Organization).filter_by(slug=org_slug).first()
    if not org or org.id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    members = db.query(User).filter_by(org_id=org.id).all()
    return [
        MemberResponse(
            id=str(m.id),
            email=m.email,
            full_name=m.full_name,
            role=m.role,
            created_at=m.created_at,
            last_login_at=m.last_login_at,
        )
        for m in members
    ]


# ── GET /team/invites ────────────────────────────────────────────────────

@router.get("/{org_slug}/invites", response_model=list[InviteResponse])
def list_invites(
    org_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les invitations en attente."""
    org = db.query(Organization).filter_by(slug=org_slug).first()
    if not org or org.id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    _require_admin(current_user)

    now = datetime.now(timezone.utc)
    invites = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.org_id == org.id,
            TeamInvite.accepted == False,  # noqa: E712
            TeamInvite.expires_at > now,
        )
        .order_by(TeamInvite.created_at.desc())
        .all()
    )
    return [
        InviteResponse(
            id=str(inv.id),
            email=inv.email,
            role=inv.role,
            invited_by_name=inv.inviter.full_name if inv.inviter else None,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            accepted=inv.accepted,
        )
        for inv in invites
    ]


# ── POST /team/invite ────────────────────────────────────────────────────

@router.post("/{org_slug}/invite", response_model=InviteResponse, status_code=201)
def invite_member(
    org_slug: str,
    body: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invite un utilisateur à rejoindre l'organisation."""
    org = db.query(Organization).filter_by(slug=org_slug).first()
    if not org or org.id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    _require_admin(current_user)

    # Vérifier si déjà membre
    existing_user = db.query(User).filter_by(email=body.email.lower(), org_id=org.id).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Cet utilisateur est déjà membre de l'organisation")

    # Vérifier si invitation en attente
    now = datetime.now(timezone.utc)
    pending = db.query(TeamInvite).filter(
        TeamInvite.org_id == org.id,
        TeamInvite.email == body.email.lower(),
        TeamInvite.accepted == False,  # noqa: E712
        TeamInvite.expires_at > now,
    ).first()
    if pending:
        raise HTTPException(status_code=409, detail="Une invitation est déjà en attente pour cet email")

    # Générer token sécurisé
    raw_token = secrets.token_urlsafe(32)
    invite = TeamInvite(
        org_id=org.id,
        email=body.email.lower(),
        token_hash=TeamInvite.hash_token(raw_token),
        role=body.role,
        invited_by=current_user.id,
        expires_at=now + timedelta(days=INVITE_TTL_DAYS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    # Envoyer l'email
    send_team_invite(
        to_email=body.email,
        inviter_name=current_user.full_name or current_user.email,
        org_name=org.name,
        invite_token=raw_token,
    )
    logger.info("team_invite_sent", org_id=str(org.id), email=body.email, role=body.role)

    return InviteResponse(
        id=str(invite.id),
        email=invite.email,
        role=invite.role,
        invited_by_name=current_user.full_name,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        accepted=invite.accepted,
    )


# ── POST /team/accept/{token} ─────────────────────────────────────────────

@router.post("/accept/{token}", status_code=200)
def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accepte une invitation (token brut de l'URL reçu par email)."""
    token_hash = TeamInvite.hash_token(token)
    now = datetime.now(timezone.utc)

    invite = db.query(TeamInvite).filter_by(token_hash=token_hash).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation introuvable ou expirée")
    if invite.accepted:
        raise HTTPException(status_code=409, detail="Cette invitation a déjà été acceptée")
    if invite.expires_at < now:
        raise HTTPException(status_code=410, detail="L'invitation a expiré")
    if invite.email != current_user.email.lower():
        raise HTTPException(status_code=403, detail="Cette invitation ne vous est pas destinée")

    # Déplacer l'utilisateur dans la nouvelle organisation
    current_user.org_id = invite.org_id
    current_user.role = invite.role
    invite.accepted = True
    db.commit()

    logger.info("team_invite_accepted", user_id=str(current_user.id), org_id=str(invite.org_id))
    return {"detail": "Invitation acceptée", "org_id": str(invite.org_id)}


# ── PATCH /team/members/{member_id}/role ──────────────────────────────────

@router.patch("/{org_slug}/members/{member_id}/role")
def update_member_role(
    org_slug: str,
    member_id: str,
    body: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change le rôle d'un membre (admin requis)."""
    org = db.query(Organization).filter_by(slug=org_slug).first()
    if not org or org.id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    _require_admin(current_user)

    try:
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="member_id invalide")

    member = db.query(User).filter_by(id=member_uuid, org_id=org.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    if member.id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas modifier votre propre rôle")

    member.role = body.role
    db.commit()
    logger.info("member_role_updated", member_id=member_id, new_role=body.role)
    return {"detail": "Rôle mis à jour", "role": body.role}


# ── DELETE /team/invites/{invite_id} ─────────────────────────────────────

@router.delete("/{org_slug}/invites/{invite_id}", status_code=204)
def cancel_invite(
    org_slug: str,
    invite_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Annule une invitation en attente."""
    org = db.query(Organization).filter_by(slug=org_slug).first()
    if not org or org.id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    _require_admin(current_user)

    try:
        invite_uuid = uuid.UUID(invite_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invite_id invalide")

    invite = db.query(TeamInvite).filter_by(id=invite_uuid, org_id=org.id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation introuvable")

    db.delete(invite)
    db.commit()
    return None
