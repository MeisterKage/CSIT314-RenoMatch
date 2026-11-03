from app.control.errors import ValidationError
from app.entity import EnquiryEntity
from app.entity.enquiry import MESSAGE_MAX_LENGTH


class ReplyEnquiryController:
    """US-47: reply to an enquiry thread, as its designer or as its customer."""

    def __init__(self):
        self.entity = EnquiryEntity

    def replyEnquiry(self, enquiryId: int, designerId: int, body: str):
        """The new message, or None when the thread is not this designer's.

        Raises ValidationError when the reply is empty or too long.
        """
        enquiry = self.entity.getEnquiry(enquiryId)
        if enquiry is None or enquiry.designerId != designerId:
            return None
        return self.reply(enquiryId, designerId, body)

    def replyAsCustomer(self, enquiryId: int, userId: int, body: str):
        """The customer-side reply, or None when the thread is not this customer's."""
        enquiry = self.entity.getEnquiry(enquiryId)
        if enquiry is None or enquiry.userId != userId:
            return None
        return self.reply(enquiryId, userId, body)

    def reply(self, enquiryId: int, senderId: int, body: str):
        body = (body or "").strip()
        if not body:
            raise ValidationError({"body": "Enter a reply."})
        if len(body) > MESSAGE_MAX_LENGTH:
            raise ValidationError(
                {"body": f"Keep the reply to {MESSAGE_MAX_LENGTH} characters or fewer."}
            )
        return self.entity.addMessage(enquiryId, senderId, body)
