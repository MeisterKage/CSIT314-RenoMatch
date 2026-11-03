# US-19 diagram text (extracted from US-19_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-19 Class Diagram
[box] «boundary» | DesignerProfilePage
[box] - controller: RateReviewDesignerController
[box] + displayReviewForm(): void | + displayReview(): void | + displayMessage(): void
[box] «control» | RateReviewDesignerController
[box] - entity: ReviewEntity
[box] + submitReview(designerId: int, userId: int, rating: int, comment: String): boolean | + checkEligibility(designerId: int, userId: int): String
[box] «entity» | ReviewEntity
[box] - reviewId: int | - designerId: int | - userId: int | - rating: int | - comment: String | - createdAt: DateTime
[box] + submitReview(designerId: int, userId: int, rating: int, comment: String): boolean | + getAverageRating(designerId: int): float | + checkEligibility(designerId: int, userId: int): String
=== US-19 Sequence Diagram
[box] Registered User
[box] : DesignerProfilePage
[box] : RateReviewDesignerController
[box] : ReviewEntity
[box] alt
[box] alt
[box] [status = eligible]
[box] [2a. never contacted this designer]
[box] [2b. already reviewed this designer]
[box] [rating selected and comment within 1,000 characters]
[box] [5a. no rating or comment too long]
[edge] 1: click "Write a Review"
[edge] 1.1: checkEligibility(designerId, userId)
[edge] 1.1.1: checkEligibility(designerId, userId)
[edge] status
[edge] status
[box] 1.2: displayReviewForm()
[box] 1.3: displayMessage()
[box] 1.4: displayReviewForm(existingReview)
[edge] 2: select rating, enter comment, click "Submit"
[edge] 2.1: submitReview(designerId, userId, rating, comment)
[edge] 2.1.1: submitReview(designerId, userId, rating, comment)
[edge] true
[edge] 2.1.2: getAverageRating(designerId)
[edge] avgRating
[edge] true
[box] 2.2: displayReview()
[edge] false
[box] 2.3: displayMessage()
```
