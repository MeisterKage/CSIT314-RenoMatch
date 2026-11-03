"""US-19: ReviewEntity.checkEligibility, submitReview and getAverageRating."""

from app.entity import EnquiryEntity, PlatformActivityEntity, ReviewEntity


def contacted(make_account, make_idp):
    customer = make_account()
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "Hello", "Is this available?")
    return customer, designer


def test_never_contacted_is_not_contacted(make_account):
    customer, designer = make_account(), make_account(role="designer")
    assert ReviewEntity.checkEligibility(designer.userId, customer.userId) == "not_contacted"


def test_contacted_is_eligible(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    assert ReviewEntity.checkEligibility(designer.userId, customer.userId) == "eligible"


def test_reviewed_is_already_reviewed(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    assert ReviewEntity.submitReview(designer.userId, customer.userId, 4, "Good") is True
    assert ReviewEntity.checkEligibility(designer.userId, customer.userId) == "already_reviewed"


def test_submit_review_stores_the_review_and_an_activity(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    assert ReviewEntity.submitReview(designer.userId, customer.userId, 5, "Lovely work") is True
    review = ReviewEntity.query.one()
    assert (review.designerId, review.userId, review.rating) == (
        designer.userId,
        customer.userId,
        5,
    )
    assert review.comment == "Lovely work"
    activities = PlatformActivityEntity.query.filter_by(
        activityType="review", userId=customer.userId
    )
    assert activities.count() == 1


def test_resubmitting_updates_the_review_without_a_second_row(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    ReviewEntity.submitReview(designer.userId, customer.userId, 2, "Slow")
    assert ReviewEntity.submitReview(designer.userId, customer.userId, 4, "Better now") is True
    review = ReviewEntity.query.one()
    assert (review.rating, review.comment) == (4, "Better now")
    assert PlatformActivityEntity.query.filter_by(activityType="review").count() == 1


def test_invalid_rating_or_comment_returns_false_and_stores_nothing(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    invalid = [(None, "x"), (0, "x"), (6, "x"), ("3", "x"), (True, "x"), (3, "x" * 1001)]
    for rating, comment in invalid:
        assert ReviewEntity.submitReview(designer.userId, customer.userId, rating, comment) is False
    assert ReviewEntity.query.count() == 0
    assert PlatformActivityEntity.query.filter_by(activityType="review").count() == 0


def test_comment_of_exactly_1000_characters_is_accepted(make_account, make_idp):
    customer, designer = contacted(make_account, make_idp)
    assert ReviewEntity.submitReview(designer.userId, customer.userId, 3, "x" * 1000) is True


def test_submit_review_refuses_a_designer_the_user_never_contacted(make_account):
    customer, designer = make_account(), make_account(role="designer")
    assert ReviewEntity.submitReview(designer.userId, customer.userId, 5, "Hi") is False
    assert ReviewEntity.query.count() == 0


def test_average_rating_follows_submissions(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    assert ReviewEntity.getAverageRating(designer.userId) == 0.0
    for rating in (5, 2):
        customer = make_account()
        EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "Hi", "Question")
        ReviewEntity.submitReview(designer.userId, customer.userId, rating, "")
    assert ReviewEntity.getAverageRating(designer.userId) == 3.5
