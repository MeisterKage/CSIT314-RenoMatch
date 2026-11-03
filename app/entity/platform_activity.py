from app.entity.db import db, utcnow

ACTIVITY_TYPES = ("view", "shortlist", "register", "enquiry", "review", "idp_added")


class PlatformActivityEntity(db.Model):
    """One event on the platform, kept for counts and reports. Never deleted.

    userId is empty for an anonymous view. idpId is empty for activity that is not
    about one IDP, such as a registration or a review.
    """

    __tablename__ = "platform_activity"

    activityId = db.Column("id", db.Integer, primary_key=True)
    activityType = db.Column("activity_type", db.String(20), nullable=False, index=True)
    userId = db.Column("user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
