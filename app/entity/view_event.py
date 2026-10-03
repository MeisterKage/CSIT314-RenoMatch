from app.entity.db import db, utcnow


class ViewEvent(db.Model):
    __tablename__ = "view_event"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    viewed_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
