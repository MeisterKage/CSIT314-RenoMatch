"""US-60 entity methods: countFeaturedIDPs and setFeatured."""

from datetime import date

from app.entity import IDPEntity, db


def test_count_featured_counts_only_active_featured_idps(make_idp):
    make_idp(isFeatured=True)
    make_idp(isFeatured=True)
    make_idp(isFeatured=False)
    make_idp(isFeatured=True, status="Suspended")
    assert IDPEntity.countFeaturedIDPs() == 2


def test_set_featured_true_features_an_active_idp_and_sets_the_date(make_idp):
    idp = make_idp()
    assert IDPEntity.setFeatured(idp.idpId, True) is True
    db.session.refresh(idp)
    assert idp.isFeatured is True
    assert idp.featuredDate == date.today()


def test_set_featured_false_unfeatures_and_keeps_the_idp_active(make_idp):
    idp = make_idp(isFeatured=True, featuredDate=date(2026, 1, 1))
    assert IDPEntity.setFeatured(idp.idpId, False) is True
    db.session.refresh(idp)
    assert idp.isFeatured is False
    assert idp.status == "Active"


def test_set_featured_returns_false_for_suspended_removed_or_missing(make_idp):
    suspended = make_idp(status="Suspended")
    removed = make_idp(status="Removed")
    assert IDPEntity.setFeatured(suspended.idpId, True) is False
    assert IDPEntity.setFeatured(removed.idpId, True) is False
    assert IDPEntity.setFeatured(9999, True) is False
    db.session.refresh(suspended)
    assert suspended.isFeatured is False
