from app.entity.db import db, utcnow


class ShortlistEvent(db.Model):
    """Recorded every time a customer saves an IDP. Never deleted."""

    __tablename__ = "shortlist_event"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    shortlisted_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
