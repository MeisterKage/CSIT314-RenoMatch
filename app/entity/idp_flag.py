from app.entity.db import db, utcnow

FLAG_STATUSES = ("open", "upheld", "dismissed")


class IDPFlag(db.Model):
    """A user's report that an IDP is inappropriate."""

    __tablename__ = "idp_flag"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="open")
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    idp = db.relationship("IDP")
    reporter = db.relationship("UserAccount", foreign_keys=[reporter_id])
    reviewer = db.relationship("UserAccount", foreign_keys=[reviewed_by])
