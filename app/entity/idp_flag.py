from sqlalchemy import select

from app.entity.db import db, utcnow

FLAG_STATUSES = ("Open", "Upheld", "Dismissed")


class IDPFlagEntity(db.Model):
    """A user's report that an IDP is inappropriate."""

    __tablename__ = "idp_flag"

    flagId = db.Column("id", db.Integer, primary_key=True)
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    reporterId = db.Column(
        "reporter_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False
    )
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="Open")
    reviewedBy = db.Column(
        "reviewed_by", db.Integer, db.ForeignKey("user_account.id"), nullable=True
    )
    reviewedAt = db.Column("reviewed_at", db.DateTime, nullable=True)
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)

    idp = db.relationship("IDPEntity")
    reporter = db.relationship("UserAccountEntity", foreign_keys=[reporterId])
    reviewer = db.relationship("UserAccountEntity", foreign_keys=[reviewedBy])

    @classmethod
    def getOpenReports(cls) -> "list[IDPFlagEntity]":
        """US-58: the Open flags, oldest first, each with its IDP and reason."""
        query = select(cls).where(cls.status == "Open").order_by(cls.createdAt, cls.flagId)
        return list(db.session.scalars(query))

    @classmethod
    def resolveReport(cls, flagId: int, managerId: int, decision: str) -> bool:
        """US-58: uphold or dismiss an Open flag and record who reviewed it and when.

        Uphold sets the IDP to Removed and clears isFeatured. Dismiss leaves the IDP alone.
        Returns False and changes nothing when the flag is missing, already resolved, or the
        decision is neither "uphold" nor "dismiss".
        """
        flag = db.session.get(cls, flagId)
        if flag is None or flag.status != "Open" or decision not in ("uphold", "dismiss"):
            return False
        if decision == "uphold":
            flag.status = "Upheld"
            flag.idp.status = "Removed"
            flag.idp.isFeatured = False
            flag.idp.featuredDate = None
        else:
            flag.status = "Dismissed"
        flag.reviewedBy = managerId
        flag.reviewedAt = utcnow()
        db.session.commit()
        return True
