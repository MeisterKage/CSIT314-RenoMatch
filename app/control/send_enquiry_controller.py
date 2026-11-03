from app.control.errors import ValidationError
from app.entity import EnquiryEntity
from app.entity.enquiry import MESSAGE_MAX_LENGTH, SUBJECT_MAX_LENGTH


class SendEnquiryController:
    """US-18: a customer asks a designer about an IDP."""

    def __init__(self):
        self.entity = EnquiryEntity

    def sendEnquiry(self, userId: int, idpId: int, subject: str, message: str):
        """The new thread, or None when the IDP is not available.

        Raises ValidationError when the subject or message is empty or too long.
        """
        subject, message = (subject or "").strip(), (message or "").strip()
        errors = {}
        if not subject:
            errors["subject"] = "Enter a subject."
        elif len(subject) > SUBJECT_MAX_LENGTH:
            errors["subject"] = f"Keep the subject to {SUBJECT_MAX_LENGTH} characters or fewer."
        if not message:
            errors["message"] = "Enter a message."
        elif len(message) > MESSAGE_MAX_LENGTH:
            errors["message"] = f"Keep the message to {MESSAGE_MAX_LENGTH} characters or fewer."
        if errors:
            raise ValidationError(errors)
        return self.entity.createEnquiry(userId, idpId, subject, message)
