from app.entity.db import db, utcnow
from app.entity.enquiry_message import EnquiryMessageEntity
from app.entity.idp import IDPEntity
from app.entity.platform_activity import PlatformActivityEntity

SUBJECT_MAX_LENGTH = 150
MESSAGE_MAX_LENGTH = 2000


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

    @classmethod
    def createEnquiry(
        cls, userId: int, idpId: int, subject: str, message: str
    ) -> "EnquiryEntity | None":
        """US-18: start a thread with the IDP's designer, with the customer's first message.

        Adds an `enquiry` PlatformActivityEntity in the same commit. Returns None when the
        IDP does not exist or is not Active.
        """
        idp = db.session.get(IDPEntity, idpId)
        if idp is None or idp.status != "Active" or not IDPEntity._designerIsPublic(idp):
            return None
        enquiry = cls(userId=userId, designerId=idp.designerId, idpId=idpId, subject=subject)
        enquiry.messages.append(EnquiryMessageEntity(senderId=userId, body=message))
        db.session.add(enquiry)
        db.session.add(PlatformActivityEntity(activityType="enquiry", userId=userId, idpId=idpId))
        db.session.commit()
        return enquiry

    @classmethod
    def getEnquiry(cls, enquiryId: int) -> "EnquiryEntity | None":
        return db.session.get(cls, enquiryId)

    @classmethod
    def getCustomerEnquiries(cls, userId: int) -> "list[EnquiryEntity]":
        """The customer's threads, the most recently active first."""
        return cls._byActivity(cls.query.filter_by(userId=userId).all())

    @classmethod
    def getDesignerEnquiries(cls, designerId: int) -> "list[EnquiryEntity]":
        """US-47: the threads addressed to the designer, the most recently active first."""
        return cls._byActivity(cls.query.filter_by(designerId=designerId).all())

    @classmethod
    def addMessage(
        cls, enquiryId: int, senderId: int, body: str
    ) -> "EnquiryMessageEntity | None":
        """US-47: add a message to a thread. None when the thread does not exist."""
        enquiry = cls.getEnquiry(enquiryId)
        if enquiry is None:
            return None
        message = EnquiryMessageEntity(enquiryId=enquiryId, senderId=senderId, body=body)
        db.session.add(message)
        db.session.commit()
        db.session.refresh(enquiry)
        return message

    @property
    def lastMessage(self) -> "EnquiryMessageEntity | None":
        return self.messages[-1] if self.messages else None

    @classmethod
    def _byActivity(cls, enquiries: "list[EnquiryEntity]") -> "list[EnquiryEntity]":
        return sorted(
            enquiries,
            key=lambda e: (e.lastMessage.sentAt if e.lastMessage else e.createdAt, e.enquiryId),
            reverse=True,
        )
