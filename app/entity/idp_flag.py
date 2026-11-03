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
