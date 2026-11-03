from app.entity import ReviewEntity


class RateReviewDesignerController:
    """US-19: check whether a user may review a designer, then save the review."""

    def __init__(self):
        self.entity = ReviewEntity

    def checkEligibility(self, designerId: int, userId: int) -> str:
        """Sequence 1.1: "eligible", "not_contacted" or "already_reviewed"."""
        return self.entity.checkEligibility(designerId, userId)

    def submitReview(self, designerId: int, userId: int, rating: int, comment: str) -> bool:
        """Sequence 2.1: submitReview, then getAverageRating when it returned true.

        The entity's submitReview does the validation (alt 5a) and returns False when the
        rating or comment is invalid.
        """
        saved = self.entity.submitReview(designerId, userId, rating, comment)
        if saved:
            self.entity.getAverageRating(designerId)
        return saved
