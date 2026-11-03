from app.entity.db import db, utcnow


class EnquiryMessageEntity(db.Model):
    """One message in an enquiry, from the customer or the designer."""

    __tablename__ = "enquiry_message"

    messageId = db.Column("id", db.Integer, primary_key=True)
    enquiryId = db.Column(
        "enquiry_id", db.Integer, db.ForeignKey("enquiry.id"), nullable=False, index=True
    )
    senderId = db.Column("sender_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sentAt = db.Column("sent_at", db.DateTime, nullable=False, default=utcnow)

    enquiry = db.relationship("EnquiryEntity", back_populates="messages")
    sender = db.relationship("UserAccountEntity")
