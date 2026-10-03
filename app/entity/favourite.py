from app.entity.db import db, utcnow


class Favourite(db.Model):
    __tablename__ = "favourite"
    __table_args__ = (
        db.UniqueConstraint("customer_id", "idp_id", name="uq_favourite_customer_idp"),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False)
    note = db.Column(db.String(255), nullable=False, default="")
    saved_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount")
    idp = db.relationship("IDP")
