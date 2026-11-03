import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAIL_KEYS = ("MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_SENDER")


class EmailService:
    """«boundary» The system's outgoing email. It sends through SMTP when every MAIL_* setting
    is configured. Otherwise it writes the email to the application log and returns True."""

    def sendEmail(self, email: str, subject: str, body: str) -> bool:
        """Used by US-05 for reset links."""
        return self.deliver(email, subject, body)

    def sendSummaryEmail(self, email: str, content: str) -> bool:
        """Used by US-48 for the weekly summary."""
        return self.deliver(email, "Your RenoMatch weekly summary", content)

    def deliver(self, email: str, subject: str, body: str) -> bool:
        config = current_app.config
        if not all(config.get(key) for key in MAIL_KEYS):
            logger.info("Email to %s | Subject: %s\n%s", email, subject, body)
            return True
        message = EmailMessage()
        message["From"] = config["MAIL_SENDER"]
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(config["MAIL_SERVER"], int(config["MAIL_PORT"]), timeout=10) as smtp:
                smtp.starttls()
                smtp.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            logger.exception("Could not send email to %s", email)
            return False
        return True
