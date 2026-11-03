"""US-19: RateReviewDesignerController makes the sequence diagram's entity calls in order."""

from app.control.rate_review_designer_controller import RateReviewDesignerController


class SpyEntity:
    def __init__(self, status="eligible", submitted=True):
        self.calls = []
        self.status = status
        self.submitted = submitted

    def checkEligibility(self, designerId, userId):
        self.calls.append(("checkEligibility", designerId, userId))
        return self.status

    def submitReview(self, designerId, userId, rating, comment):
        self.calls.append(("submitReview", designerId, userId, rating, comment))
        return self.submitted

    def getAverageRating(self, designerId):
        self.calls.append(("getAverageRating", designerId))
        return 4.0


def controllerWith(spy):
    controller = RateReviewDesignerController()
    controller.entity = spy
    return controller


def test_check_eligibility_calls_the_entity_once_and_returns_its_status():
    spy = SpyEntity(status="already_reviewed")
    assert controllerWith(spy).checkEligibility(7, 3) == "already_reviewed"
    assert spy.calls == [("checkEligibility", 7, 3)]


def test_submit_review_true_calls_submit_then_average():
    spy = SpyEntity(submitted=True)
    assert controllerWith(spy).submitReview(7, 3, 5, "Great") is True
    assert spy.calls == [("submitReview", 7, 3, 5, "Great"), ("getAverageRating", 7)]


def test_submit_review_false_does_not_ask_for_the_average():
    spy = SpyEntity(submitted=False)
    assert controllerWith(spy).submitReview(7, 3, 9, "Great") is False
    assert spy.calls == [("submitReview", 7, 3, 9, "Great")]
