from app.entity.db import db, utcnow


class FavouriteEntity(db.Model):
    """An IDP a user has saved, with an optional note. One per (userId, idpId)."""

    __tablename__ = "favourite"
    __table_args__ = (db.UniqueConstraint("user_id", "idp_id", name="uq_favourite_user_idp"),)

    favouriteId = db.Column("id", db.Integer, primary_key=True)
    userId = db.Column(
        "user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=False)
    note = db.Column(db.String(255), nullable=False, default="")
    savedAt = db.Column("saved_at", db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("UserAccountEntity")
    idp = db.relationship("IDPEntity")
