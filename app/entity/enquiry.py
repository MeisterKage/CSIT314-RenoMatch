from app.entity.db import db, utcnow


class Enquiry(db.Model):
    __tablename__ = "enquiry"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=True)
    subject = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount", foreign_keys=[customer_id])
    designer = db.relationship("UserAccount", foreign_keys=[designer_id])
    idp = db.relationship("IDP")
    messages = db.relationship(
        "EnquiryMessage",
        back_populates="enquiry",
        order_by="EnquiryMessage.sent_at",
        cascade="all, delete-orphan",
    )


class EnquiryMessage(db.Model):
    __tablename__ = "enquiry_message"

    id = db.Column(db.Integer, primary_key=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey("enquiry.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    enquiry = db.relationship("Enquiry", back_populates="messages")
    sender = db.relationship("UserAccount")
