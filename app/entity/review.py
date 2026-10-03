from app.entity.db import db, utcnow


class Review(db.Model):
    __tablename__ = "review"
    __table_args__ = (db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),)

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount", foreign_keys=[customer_id])
    designer = db.relationship("UserAccount", foreign_keys=[designer_id])
