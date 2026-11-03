from app.entity.db import db, utcnow


class EnquiryEntity(db.Model):
    """A conversation a user (the customer) starts with a designer."""

    __tablename__ = "enquiry"

    enquiryId = db.Column("id", db.Integer, primary_key=True)
    userId = db.Column(
        "user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    designerId = db.Column(
        "designer_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=True)
    subject = db.Column(db.String(150), nullable=False)
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("UserAccountEntity", foreign_keys=[userId])
    designer = db.relationship("UserAccountEntity", foreign_keys=[designerId])
    idp = db.relationship("IDPEntity")
    messages = db.relationship(
        "EnquiryMessageEntity",
        back_populates="enquiry",
        order_by="EnquiryMessageEntity.sentAt",
        cascade="all, delete-orphan",
    )
