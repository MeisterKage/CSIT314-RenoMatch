from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.entity.db import db, utcnow
from app.entity.enquiry import EnquiryEntity
from app.entity.platform_activity import PlatformActivityEntity

COMMENT_MAX_LENGTH = 1000


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

    @classmethod
    def checkEligibility(cls, designerId: int, userId: int) -> str:
        """US-19: "already_reviewed", "eligible" (has an enquiry with the designer) or
        "not_contacted"."""
        if cls.query.filter_by(designerId=designerId, userId=userId).first() is not None:
            return "already_reviewed"
        if EnquiryEntity.query.filter_by(designerId=designerId, userId=userId).first() is None:
            return "not_contacted"
        return "eligible"

    @classmethod
    def submitReview(cls, designerId: int, userId: int, rating: int, comment: str) -> bool:
        """US-19: save the user's review of the designer, or update it when one exists.

        Returns False, saving nothing, when the rating is not a whole number from 1 to 5
        (step 5a), the comment is longer than 1,000 characters (5a) or the user has never
        contacted the designer. A new review also adds a `review` PlatformActivityEntity.
        """
        if not isinstance(rating, int) or isinstance(rating, bool) or not 1 <= rating <= 5:
            return False
        comment = (comment or "").strip()
        if len(comment) > COMMENT_MAX_LENGTH:
            return False
        status = cls.checkEligibility(designerId, userId)
        if status == "not_contacted":
            return False
        if status == "already_reviewed":
            cls._update(designerId, userId, rating, comment)
            return True
        db.session.add(cls(designerId=designerId, userId=userId, rating=rating, comment=comment))
        db.session.add(PlatformActivityEntity(activityType="review", userId=userId))
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent submission by the same user won the race: update that review.
            db.session.rollback()
            cls._update(designerId, userId, rating, comment)
        return True

    @classmethod
    def _update(cls, designerId: int, userId: int, rating: int, comment: str) -> None:
        review = cls.query.filter_by(designerId=designerId, userId=userId).one()
        review.rating = rating
        review.comment = comment
        db.session.commit()

    @classmethod
    def getAverageRating(cls, designerId: int) -> float:
        """The mean rating of a designer's reviews, or 0.0 when there are none."""
        average = (
            db.session.query(func.avg(cls.rating)).filter(cls.designerId == designerId).scalar()
        )
        return float(average) if average is not None else 0.0

    @classmethod
    def getReviews(cls, designerId: int) -> "list[ReviewEntity]":
        """A designer's reviews, newest first."""
        return (
            db.session.query(cls)
            .filter_by(designerId=designerId)
            .order_by(cls.createdAt.desc(), cls.reviewId.desc())
            .all()
        )
