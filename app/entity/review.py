from app.entity.db import db, utcnow


class ReviewEntity(db.Model):
    """A user's rating (1-5) and comment on a designer. One per (designerId, userId)."""

    __tablename__ = "review"
    __table_args__ = (
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),
        db.UniqueConstraint("designer_id", "user_id", name="uq_review_designer_user"),
    )

    reviewId = db.Column("id", db.Integer, primary_key=True)
    designerId = db.Column(
        "designer_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    userId = db.Column("user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False, default="")
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)

    designer = db.relationship("UserAccountEntity", foreign_keys=[designerId])
    user = db.relationship("UserAccountEntity", foreign_keys=[userId])
