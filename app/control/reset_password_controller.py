import logging

from flask import url_for

from app.boundary.email_service import EmailService
from app.control.validation import password_problem
from app.entity import UserAccountEntity

logger = logging.getLogger(__name__)

SENT_MESSAGE = "If that email is registered, we have sent a reset link. Check your inbox."
EXPIRED_MESSAGE = "This reset link is invalid or has expired. Request a new one."


class ResetPasswordController:
    """US-05: reset a forgotten password. `message` holds the reason for the last failure."""

    def __init__(self):
        self.entity = UserAccountEntity
        self.emailService = EmailService()
        self.message = ""
        self.issuedToken = None

    def requestPasswordReset(self, email: str) -> bool:
        """1.1: ask the entity (1.1.1). If the email is registered, send the link (1.1.2).
        True is returned either way, so the page cannot be used to find registered emails."""
        self.issuedToken = self.entity.requestPasswordReset(email)
        if self.issuedToken:
            self.sendResetLink(email)
        return True

    def resetPassword(self, token: str, newPassword: str) -> bool:
        """2.1: validate the password (2.1.1). Only when valid, ask the entity (2.1.2) and
        return its result. An invalid password returns False (9b)."""
        if not self.validatePassword(newPassword):
            return False
        result = self.entity.resetPassword(token, newPassword)
        if not result:
            self.message = EXPIRED_MESSAGE
        return result

    def sendResetLink(self, email: str) -> None:
        """Private: email the /reset-password/<token> link through EmailService.sendEmail."""
        try:
            link = url_for("reset_password.reset", token=self.issuedToken, _external=True)
            sent = self.emailService.sendEmail(
                email,
                "Reset your RenoMatch password",
                f"Use this link within 1 hour to choose a new password:\n{link}\n\n"
                "If you did not ask for this, you can ignore this email.",
            )
            if not sent:
                logger.warning("The password reset email could not be sent.")
        finally:
            self.issuedToken = None

    def validatePassword(self, newPassword: str) -> bool:
        """Private: the existing password rules. The page passes an empty password when the
        confirmation does not match, which fails here too."""
        problem = password_problem(newPassword)
        self.message = problem or ""
        return problem is None
