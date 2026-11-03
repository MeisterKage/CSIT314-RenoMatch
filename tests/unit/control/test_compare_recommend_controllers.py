"""US-12 and US-13: the controllers make the sequence diagram's entity calls in order."""

from app.control.compare_idps_controller import CompareIDPsController
from app.control.view_recommended_idps_controller import ViewRecommendedIDPsController


class SpyEntity:
    def __init__(self, recommended=None, popular=None, compared=None):
        self.calls = []
        self.recommended = recommended
        self.popular = popular or []
        self.compared = compared or []

    def getRecommendedIDPs(self, userId):
        self.calls.append(("getRecommendedIDPs", userId))
        return self.recommended

    def getPopularIDPs(self):
        self.calls.append(("getPopularIDPs",))
        return self.popular

    def compareIDPs(self, idpIds):
        self.calls.append(("compareIDPs", idpIds))
        return self.compared


def recommendController(spy):
    controller = ViewRecommendedIDPsController()
    controller.entity = spy
    return controller


def test_compare_passes_the_ids_to_the_entity():
    spy = SpyEntity(compared=["a", "b"])
    controller = CompareIDPsController()
    controller.entity = spy
    assert controller.compareIDPs([1, 2]) == ["a", "b"]
    assert spy.calls == [("compareIDPs", [1, 2])]


def test_recommended_not_empty_skips_popular():
    spy = SpyEntity(recommended=["x"])
    result = recommendController(spy).getRecommendedIDPs(7)
    assert result.recommendedIdps == ["x"] and result.popularIdps is None
    assert spy.calls == [("getRecommendedIDPs", 7)]


def test_no_history_asks_for_popular_after_recommended():
    spy = SpyEntity(recommended=[], popular=["p"])
    result = recommendController(spy).getRecommendedIDPs(7)
    assert result.recommendedIdps == [] and result.popularIdps == ["p"]
    assert spy.calls == [("getRecommendedIDPs", 7), ("getPopularIDPs",)]


def test_no_matching_idps_returns_nothing_and_never_asks_for_popular():
    spy = SpyEntity(recommended=None)
    result = recommendController(spy).getRecommendedIDPs(7)
    assert result.recommendedIdps is None and result.popularIdps is None
    assert spy.calls == [("getRecommendedIDPs", 7)]
