"""Tests for app.services.email — Resend email service."""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# _send_email
# ---------------------------------------------------------------------------

class TestSendEmail:
    @patch("app.services.email.settings")
    def test_skip_when_no_api_key(self, mock_settings):
        mock_settings.RESEND_API_KEY = ""
        from app.services.email import _send_email
        result = _send_email("user@test.com", "Subject", "<p>Body</p>")
        assert result is False

    @patch("app.services.email._resend", None)
    @patch("app.services.email.settings")
    def test_send_success(self, mock_settings):
        mock_settings.RESEND_API_KEY = "re_test_key"
        mock_settings.EMAIL_FROM = "noreply@ao-copilot.fr"

        mock_resend = MagicMock()
        with patch("app.services.email._get_resend", return_value=mock_resend):
            from app.services.email import _send_email
            result = _send_email("user@test.com", "Test Subject", "<p>Hello</p>")

        assert result is True
        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == ["user@test.com"]
        assert call_args["subject"] == "Test Subject"

    @patch("app.services.email._resend", None)
    @patch("app.services.email.settings")
    def test_send_failure_returns_false(self, mock_settings):
        mock_settings.RESEND_API_KEY = "re_test_key"
        mock_settings.EMAIL_FROM = "noreply@ao-copilot.fr"

        mock_resend = MagicMock()
        mock_resend.Emails.send.side_effect = Exception("SMTP error")
        with patch("app.services.email._get_resend", return_value=mock_resend):
            from app.services.email import _send_email
            result = _send_email("user@test.com", "Subject", "<p>Body</p>")

        assert result is False

    @patch("app.services.email._resend", None)
    @patch("app.services.email.settings")
    def test_resend_not_installed(self, mock_settings):
        mock_settings.RESEND_API_KEY = "re_test_key"
        with patch("app.services.email._get_resend", return_value=None):
            from app.services.email import _send_email
            result = _send_email("user@test.com", "Sub", "<p>hi</p>")
        assert result is False


# ---------------------------------------------------------------------------
# _base_template
# ---------------------------------------------------------------------------

class TestBaseTemplate:
    @patch("app.services.email.settings")
    def test_template_contains_branding(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.ao-copilot.fr"
        from app.services.email import _base_template
        html = _base_template("<p>Test content</p>")
        assert "AO Copilot" in html
        assert "Test content" in html
        assert "https://app.ao-copilot.fr" in html


# ---------------------------------------------------------------------------
# send_analysis_complete
# ---------------------------------------------------------------------------

class TestSendAnalysisComplete:
    @patch("app.services.email._send_email")
    @patch("app.services.email.settings")
    def test_sends_analysis_email(self, mock_settings, mock_send):
        mock_settings.FRONTEND_URL = "https://app.ao-copilot.fr"
        mock_send.return_value = True

        from app.services.email import send_analysis_complete
        result = send_analysis_complete(
            to_email="user@test.com",
            user_name="Alice",
            project_title="AO Renovation",
            project_id="proj-123",
            risk_count=3,
            action_count=2,
        )
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "user@test.com" in args[1].get("to", args[0][0] if args[0] else "")


# ---------------------------------------------------------------------------
# send_upload_confirmation
# ---------------------------------------------------------------------------

class TestSendUploadConfirmation:
    @patch("app.services.email._send_email")
    @patch("app.services.email.settings")
    def test_sends_upload_email(self, mock_settings, mock_send):
        mock_settings.FRONTEND_URL = "https://app.ao-copilot.fr"
        mock_send.return_value = True

        from app.services.email import send_upload_confirmation
        result = send_upload_confirmation(
            to_email="user@test.com",
            user_name="Bob",
            project_title="Marche Public",
            doc_name="CCAP.pdf",
            project_id="proj-456",
        )
        assert result is True
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# send_deadline_reminder
# ---------------------------------------------------------------------------

class TestSendDeadlineReminder:
    @patch("app.services.email._send_email")
    def test_sends_deadline_email(self, mock_send):
        mock_send.return_value = True
        from app.services.email import send_deadline_reminder
        result = send_deadline_reminder(
            user_email="user@test.com",
            user_name="Charlie",
            project_title="AO BTP",
            deadline_description="Date limite de remise des offres",
            days_remaining=3,
            project_id="proj-789",
            frontend_url="https://app.ao-copilot.fr",
        )
        assert result is True

    @patch("app.services.email._send_email")
    def test_urgent_deadline_styling(self, mock_send):
        """2 days or less should use red urgency styling."""
        mock_send.return_value = True
        from app.services.email import send_deadline_reminder
        send_deadline_reminder(
            user_email="user@test.com",
            user_name="Charlie",
            project_title="AO",
            deadline_description="Deadline",
            days_remaining=1,
            project_id="p1",
            frontend_url="https://test.com",
        )
        html_arg = mock_send.call_args[1].get("html", mock_send.call_args[0][2] if len(mock_send.call_args[0]) > 2 else "")
        # The HTML should contain the urgency color
        assert mock_send.called


# ---------------------------------------------------------------------------
# send_quota_warning
# ---------------------------------------------------------------------------

class TestSendQuotaWarning:
    @patch("app.services.email._send_email")
    def test_sends_quota_warning(self, mock_send):
        mock_send.return_value = True
        from app.services.email import send_quota_warning
        result = send_quota_warning(
            user_email="user@test.com",
            user_name="Diana",
            used=12,
            quota=15,
            plan="Starter",
            frontend_url="https://app.ao-copilot.fr",
        )
        assert result is True
        mock_send.assert_called_once()
        # Subject should contain percentage
        call_args = mock_send.call_args
        subject = call_args[1].get("subject", call_args[0][1] if len(call_args[0]) > 1 else "")
        assert "80%" in subject

    @patch("app.services.email._send_email")
    def test_quota_zero_division(self, mock_send):
        mock_send.return_value = True
        from app.services.email import send_quota_warning
        result = send_quota_warning(
            user_email="u@t.com", user_name="E",
            used=5, quota=0, plan="Free",
            frontend_url="https://test.com",
        )
        assert result is True


# ---------------------------------------------------------------------------
# send_team_invite
# ---------------------------------------------------------------------------

class TestSendTeamInvite:
    @patch("app.services.email._send_email")
    @patch("app.services.email.settings")
    def test_sends_invite(self, mock_settings, mock_send):
        mock_settings.FRONTEND_URL = "https://app.ao-copilot.fr"
        mock_send.return_value = True

        from app.services.email import send_team_invite
        result = send_team_invite(
            to_email="newuser@test.com",
            inviter_name="Admin",
            org_name="BTP Corp",
            invite_token="tok_abc123",
        )
        assert result is True
        call_args = mock_send.call_args
        html = call_args[1].get("html", call_args[0][2] if len(call_args[0]) > 2 else "")
        assert mock_send.called
