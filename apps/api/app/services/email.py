"""Service d'envoi d'emails via Resend (transactionnel)."""
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)

# ── Lazy Resend init ───────────────────────────────────────────────────
_resend = None


def _get_resend():
    global _resend
    if _resend is None:
        try:
            import resend as resend_lib
            resend_lib.api_key = settings.RESEND_API_KEY
            _resend = resend_lib
        except ImportError:
            logger.error("resend_not_installed", hint="pip install resend>=2.0.0")
            return None
    return _resend


def _send_email(to: str, subject: str, html: str) -> bool:
    """Envoie un email. Retourne True si succès, False si erreur."""
    if not settings.RESEND_API_KEY:
        logger.warning("resend_api_key_missing", action="skip_email_send")
        return False

    resend = _get_resend()
    if not resend:
        return False

    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_send_failed", to=to, subject=subject, error=str(exc))
        return False


# ── Templates HTML ─────────────────────────────────────────────────────

def _base_template(content: str, preview: str = "") -> str:
    """Template HTML de base avec branding AO Copilot."""
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:40px 20px;">

    <!-- Logo -->
    <div style="text-align:center;margin-bottom:32px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="background:#1E40AF;border-radius:10px;width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;">
          <span style="color:white;font-weight:bold;font-size:14px;">AO</span>
        </div>
        <span style="color:#1E40AF;font-weight:700;font-size:18px;">AO Copilot</span>
      </div>
    </div>

    <!-- Content card -->
    <div style="background:white;border-radius:16px;padding:32px;border:1px solid #E2E8F0;box-shadow:0 1px 3px rgba(0,0,0,0.07);">
      {content}
    </div>

    <!-- Footer -->
    <div style="text-align:center;margin-top:24px;color:#94A3B8;font-size:12px;">
      <p>AO Copilot — Analyse automatique de DCE BTP</p>
      <p><a href="{settings.FRONTEND_URL}" style="color:#1E40AF;text-decoration:none;">ao-copilot.fr</a>
         &nbsp;|&nbsp;
         <a href="{settings.FRONTEND_URL}/settings" style="color:#94A3B8;text-decoration:none;">Gérer mes notifications</a>
      </p>
    </div>
  </div>
</body>
</html>
"""


# ── Fonctions d'envoi ──────────────────────────────────────────────────

def send_analysis_complete(
    to_email: str,
    user_name: str,
    project_title: str,
    project_id: str,
    risk_count: int = 0,
    action_count: int = 0,
) -> bool:
    """Email envoyé quand l'analyse IA est terminée."""
    project_url = f"{settings.FRONTEND_URL}/projects/{project_id}"

    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Analyse terminée ! ✅</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 24px;line-height:1.6;">
      Bonjour {user_name},<br>
      L&apos;analyse de votre projet <strong style="color:#1E3A8A">{project_title}</strong>
      est maintenant disponible.
    </p>

    <!-- Stats rapides -->
    <div style="display:flex;gap:12px;margin-bottom:24px;">
      {'<div style="flex:1;background:#FEF2F2;border-radius:10px;padding:12px;text-align:center;"><p style="margin:0;font-size:20px;font-weight:800;color:#DC2626;">' + str(risk_count) + '</p><p style="margin:0;font-size:11px;color:#EF4444;font-weight:600;">Risques détectés</p></div>' if risk_count > 0 else ""}
      {'<div style="flex:1;background:#EFF6FF;border-radius:10px;padding:12px;text-align:center;"><p style="margin:0;font-size:20px;font-weight:800;color:#1E40AF;">' + str(action_count) + '</p><p style="margin:0;font-size:11px;color:#3B82F6;font-weight:600;">Actions sous 48h</p></div>' if action_count > 0 else ""}
    </div>

    <a href="{project_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Voir l&apos;analyse →
    </a>
    """

    return _send_email(
        to=to_email,
        subject=f"✅ Analyse terminée — {project_title}",
        html=_base_template(content),
    )


def send_upload_confirmation(
    to_email: str,
    user_name: str,
    project_title: str,
    doc_name: str,
    project_id: str,
) -> bool:
    """Email de confirmation après upload d'un document."""
    project_url = f"{settings.FRONTEND_URL}/projects/{project_id}"

    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Document reçu 📄</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 24px;line-height:1.6;">
      Bonjour {user_name},<br>
      Le document <strong style="color:#1E3A8A">{doc_name}</strong> a bien été
      importé dans le projet <strong>{project_title}</strong>.
      L&apos;extraction du texte est en cours.
    </p>

    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:14px 16px;margin-bottom:24px;">
      <p style="margin:0;color:#15803D;font-size:13px;font-weight:600;">
        ⏱ Temps d&apos;analyse estimé : 2-5 minutes selon la taille du document
      </p>
    </div>

    <a href="{project_url}"
       style="display:inline-block;background:#F8FAFC;border:1px solid #E2E8F0;color:#1E40AF;
              font-weight:600;font-size:14px;padding:12px 24px;border-radius:10px;text-decoration:none;">
      Suivre l&apos;avancement →
    </a>
    """

    return _send_email(
        to=to_email,
        subject=f"Document importé — {doc_name}",
        html=_base_template(content),
    )


def send_deadline_reminder(
    user_email: str,
    user_name: str,
    project_title: str,
    deadline_description: str,
    days_remaining: int,
    project_id: str,
    frontend_url: str,
) -> bool:
    """Rappel J-7 deadline : envoyé quand une échéance approche dans <= 7 jours."""
    project_url = f"{frontend_url}/projects/{project_id}"

    urgency_color = "#DC2626" if days_remaining <= 2 else "#F59E0B"
    urgency_bg = "#FEF2F2" if days_remaining <= 2 else "#FEF3C7"
    urgency_border = "#FECACA" if days_remaining <= 2 else "#F59E0B"
    urgency_text_color = "#92400E" if days_remaining > 2 else "#7F1D1D"

    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Deadline dans {days_remaining} jour(s) ⏰</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 20px;line-height:1.6;">
      Bonjour {user_name},<br>
      Un délai important approche pour <strong style="color:#1E3A8A">{project_title}</strong>.
    </p>

    <div style="background:{urgency_bg};border:1px solid {urgency_border};padding:16px;border-radius:8px;margin:16px 0;">
      <p style="margin:0 0 6px;font-weight:700;color:#0F172A;font-size:15px;">📋 {deadline_description}</p>
      <p style="margin:0;color:{urgency_text_color};font-weight:600;font-size:14px;">
        ⏰ Dans {days_remaining} jour(s)
      </p>
    </div>

    <a href="{project_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Voir le projet →
    </a>
    """

    return _send_email(
        to=user_email,
        subject=f"⏰ Deadline dans {days_remaining}j — {project_title}",
        html=_base_template(content),
    )


def send_quota_warning(
    user_email: str,
    user_name: str,
    used: int,
    quota: int,
    plan: str,
    frontend_url: str,
) -> bool:
    """Alerte quota à 80% — prévient l'utilisateur d'upgrader ou de libérer de l'espace."""
    pct = int(used / quota * 100) if quota > 0 else 100
    billing_url = f"{frontend_url}/settings/billing"

    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Quota presque atteint ⚠️</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 20px;line-height:1.6;">
      Bonjour {user_name},<br>
      Votre quota de documents est utilisé à <strong style="color:#B45309">{pct}%</strong>
      sur votre plan <strong>{plan}</strong>.
    </p>

    <!-- Barre de progression -->
    <div style="background:#F1F5F9;border-radius:99px;height:12px;margin-bottom:8px;overflow:hidden;">
      <div style="background:{'#EF4444' if pct >= 90 else '#F59E0B'};height:100%;width:{min(pct, 100)}%;border-radius:99px;transition:width 0.3s;"></div>
    </div>
    <p style="text-align:center;color:#64748B;font-size:13px;margin:0 0 20px;">
      {used} / {quota} documents utilisés
    </p>

    <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:14px 16px;margin-bottom:24px;">
      <p style="margin:0;color:#92400E;font-size:13px;font-weight:600;">
        💡 Passez à un plan supérieur pour continuer à analyser vos DCE sans interruption.
      </p>
    </div>

    <a href="{billing_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Upgrader mon plan →
    </a>
    """

    return _send_email(
        to=user_email,
        subject=f"⚠️ Quota à {pct}% — {used}/{quota} documents",
        html=_base_template(content),
    )


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """Email de réinitialisation de mot de passe."""
    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Réinitialisation de mot de passe 🔑</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 24px;line-height:1.6;">
      Bonjour,<br>
      Vous avez demandé la réinitialisation de votre mot de passe sur AO Copilot.
      Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
    </p>

    <a href="{reset_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Réinitialiser mon mot de passe →
    </a>

    <div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:10px;padding:14px 16px;margin-top:24px;">
      <p style="margin:0;color:#92400E;font-size:13px;font-weight:600;">
        ⏱ Ce lien est valable 15 minutes. Si vous n&apos;avez pas demandé cette réinitialisation,
        ignorez simplement cet email.
      </p>
    </div>
    """

    return _send_email(
        to=to_email,
        subject="Réinitialisation de mot de passe — AO Copilot",
        html=_base_template(content),
    )


def send_verification_email(email: str, verify_url: str) -> bool:
    """Email de vérification d'adresse email après inscription."""
    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">V&eacute;rifiez votre adresse email</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 24px;line-height:1.6;">
      Bienvenue sur AO Copilot !<br>
      Cliquez sur le bouton ci-dessous pour confirmer votre adresse email
      et activer toutes les fonctionnalit&eacute;s de votre compte.
    </p>

    <a href="{verify_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Confirmer mon email
    </a>

    <p style="color:#94A3B8;font-size:12px;margin-top:20px;">
      Ce lien est valable 24 heures. Si vous n&apos;avez pas cr&eacute;&eacute; de compte sur AO Copilot,
      ignorez simplement cet email.
    </p>
    """

    return _send_email(
        to=email,
        subject="Confirmez votre adresse email \u2014 AO Copilot",
        html=_base_template(content),
    )


def send_team_invite(
    to_email: str,
    inviter_name: str,
    org_name: str,
    invite_token: str,
) -> bool:
    """Email d'invitation à rejoindre une organisation."""
    invite_url = f"{settings.FRONTEND_URL}/invite/{invite_token}"

    content = f"""
    <h2 style="margin:0 0 8px;font-size:22px;color:#0F172A;">Invitation à rejoindre {org_name} 🤝</h2>
    <p style="color:#64748B;font-size:15px;margin:0 0 24px;line-height:1.6;">
      Bonjour,<br>
      <strong>{inviter_name}</strong> vous invite à rejoindre
      l&apos;espace <strong style="color:#1E3A8A">{org_name}</strong> sur AO Copilot.
    </p>

    <a href="{invite_url}"
       style="display:inline-block;background:linear-gradient(135deg,#1E40AF,#1D4ED8);color:white;
              font-weight:600;font-size:15px;padding:14px 28px;border-radius:12px;text-decoration:none;
              box-shadow:0 4px 12px rgba(30,64,175,0.3);">
      Accepter l&apos;invitation →
    </a>

    <p style="color:#94A3B8;font-size:12px;margin-top:20px;">
      Ce lien est valable 7 jours. Si vous n&apos;attendiez pas cette invitation, ignorez simplement cet email.
    </p>
    """

    return _send_email(
        to=to_email,
        subject=f"Invitation à rejoindre {org_name} sur AO Copilot",
        html=_base_template(content),
    )
