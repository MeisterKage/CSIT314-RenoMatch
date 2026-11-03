from flask import url_for

from app.boundary.email_service import EmailService
from app.control.validation import password_problem
from app.entity import UserAccountEntity

SENT_MESSAGE = "If that email is registered, we have sent a reset link. Check your inbox."
EXPIRED_MESSAGE = "This reset link is invalid or has expired. Request a new one."


class ResetPasswordController:
    """US-05: reset a forgotten password. `message` holds the reason for the last failure."""

    def __init__(self):
        self.entity = UserAccountEntity
        self.emailService = EmailService()
        self.message = ""

    def requestPasswordReset(self, email: str) -> bool:
        """1.1: ask the entity (1.1.1). If the email is registered, send the link (1.1.2).
        True is returned either way, so the page cannot be used to find registered emails."""
        emailFound = self.entity.requestPasswordReset(email)
        if emailFound:
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
        token = self.entity.takeIssuedResetToken(email)
        if token is None:
            return
        link = url_for("reset_password.reset", token=token, _external=True)
        self.emailService.sendEmail(
            email,
            "Reset your RenoMatch password",
            f"Use this link within 1 hour to choose a new password:\n{link}\n\n"
            "If you did not ask for this, you can ignore this email.",
        )

    def validatePassword(self, newPassword: str) -> bool:
        """Private: the existing password rules. The page passes an empty password when the
        confirmation does not match, which fails here too."""
        problem = password_problem(newPassword)
        self.message = problem or ""
        return problem is None
