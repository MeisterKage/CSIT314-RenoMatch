"""US-60 FeatureIDPController: call order and alt guards of the sequence diagram."""

from app.control.feature_idp_controller import FeatureIDPController
from app.entity import IDPEntity


def spy(monkeypatch, calls, name):
    original = getattr(IDPEntity, name)

    def wrapper(*args):
        calls.append((name, *args))
        return original(*args)

    monkeypatch.setattr(IDPEntity, name, staticmethod(wrapper))


def test_feature_counts_then_sets_featured_true(app, make_idp, monkeypatch):
    idp = make_idp()
    calls = []
    spy(monkeypatch, calls, "countFeaturedIDPs")
    spy(monkeypatch, calls, "setFeatured")
    assert FeatureIDPController().featureIDP(idp.idpId) is True
    assert calls == [("countFeaturedIDPs",), ("setFeatured", idp.idpId, True)]


def test_feature_with_six_already_featured_returns_false_without_setting(
    app, make_idp, monkeypatch
):
    for _ in range(6):
        make_idp(isFeatured=True)
    idp = make_idp()
    calls = []
    spy(monkeypatch, calls, "setFeatured")
    controller = FeatureIDPController()
    assert controller.featureIDP(idp.idpId) is False
    assert calls == []
    assert controller.limitReached is True


def test_feature_returns_the_entity_result_when_the_idp_is_suspended(app, make_idp):
    idp = make_idp(status="Suspended")
    controller = FeatureIDPController()
    assert controller.featureIDP(idp.idpId) is False
    assert controller.limitReached is False


def test_five_featured_still_allows_one_more(app, make_idp):
    for _ in range(5):
        make_idp(isFeatured=True)
    idp = make_idp()
    assert FeatureIDPController().featureIDP(idp.idpId) is True


def test_unfeature_calls_set_featured_false(app, make_idp, monkeypatch):
    idp = make_idp(isFeatured=True)
    calls = []
    spy(monkeypatch, calls, "setFeatured")
    assert FeatureIDPController().unfeatureIDP(idp.idpId) is True
    assert calls == [("setFeatured", idp.idpId, False)]
