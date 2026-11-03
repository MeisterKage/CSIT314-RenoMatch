"""US-12 and US-13: IDPEntity.compareIDPs, getRecommendedIDPs, getPopularIDPs, getFeaturedIDPs."""

from app.entity import FavouriteEntity, IDPEntity, PlatformActivityEntity, db


def view(userId, idp):
    db.session.add(PlatformActivityEntity(activityType="view", userId=userId, idpId=idp.idpId))
    db.session.commit()


def test_compare_returns_active_idps_in_the_order_given(make_idp):
    a, b, c = make_idp(), make_idp(), make_idp()
    assert IDPEntity.compareIDPs([c.idpId, a.idpId, b.idpId]) == [c, a, b]


def test_compare_leaves_out_idps_that_are_not_active_or_missing(make_idp):
    a, b = make_idp(), make_idp(status="Suspended")
    c = make_idp(status="Removed")
    assert IDPEntity.compareIDPs([a.idpId, b.idpId, c.idpId, 9999]) == [a]


def test_popular_is_top_ten_active_by_view_count(make_idp):
    idps = [make_idp(viewCount=n) for n in range(12)]
    make_idp(viewCount=500, status="Removed")
    assert IDPEntity.getPopularIDPs() == list(reversed(idps))[:10]


def test_featured_is_six_active_featured_idps(make_idp):
    for _ in range(8):
        make_idp(isFeatured=True)
    make_idp(isFeatured=False)
    make_idp(isFeatured=True, status="Suspended")
    featured = IDPEntity.getFeaturedIDPs()
    assert len(featured) == 6
    assert all(idp.isFeatured and idp.status == "Active" for idp in featured)


def test_recommended_is_empty_list_with_no_history(make_account, make_idp):
    user = make_account()
    make_idp()
    assert IDPEntity.getRecommendedIDPs(user.userId) == []


def test_recommended_is_none_with_history_but_no_match(make_account, make_idp, make_category):
    user = make_account()
    seen = make_idp(style="Modern", category=make_category())
    make_idp(style="Luxury", category=make_category())
    view(user.userId, seen)
    FavouriteEntity.saveFavourite(user.userId, seen.idpId, "")
    assert IDPEntity.getRecommendedIDPs(user.userId) is None


def test_recommended_ranks_by_matches_then_view_count(make_account, make_idp, make_category):
    user = make_account()
    cat, other = make_category(), make_category()
    seen = make_idp(style="Modern", category=cat)
    FavouriteEntity.saveFavourite(user.userId, seen.idpId, "")
    both_low = make_idp(style="Modern", category=cat, viewCount=1)
    both_high = make_idp(style="Modern", category=cat, viewCount=9)
    style_only_hot = make_idp(style="Modern", category=other, viewCount=500)
    category_only = make_idp(style="Luxury", category=cat, viewCount=100)
    make_idp(style="Luxury", category=other, viewCount=900)
    assert IDPEntity.getRecommendedIDPs(user.userId) == [
        both_high,
        both_low,
        style_only_hot,
        category_only,
    ]


def test_recommended_excludes_saved_and_inactive_idps(make_account, make_idp, make_category):
    user = make_account()
    cat = make_category()
    for _ in range(2):
        saved = make_idp(style="Modern", category=cat)
        FavouriteEntity.saveFavourite(user.userId, saved.idpId, "")
    make_idp(style="Modern", category=cat, status="Suspended")
    candidate = make_idp(style="Modern", category=cat)
    assert IDPEntity.getRecommendedIDPs(user.userId) == [candidate]


def test_recommended_is_limited_to_ten(make_account, make_idp, make_category):
    user = make_account()
    cat = make_category()
    view(user.userId, make_idp(category=cat))
    for _ in range(12):
        make_idp(category=cat)
    assert len(IDPEntity.getRecommendedIDPs(user.userId)) == 10


def test_recommended_ignores_other_users_history(make_account, make_idp):
    user, other = make_account(), make_account()
    view(other.userId, make_idp())
    assert IDPEntity.getRecommendedIDPs(user.userId) == []
