"""Wrap-up fixes: search escaping, hidden designers, weekly stats, notes, registration."""

import pytest

from app.entity import (
    FavouriteEntity,
    IDPEntity,
    PlatformActivityEntity,
    UserAccountEntity,
    db,
)


def titles(page):
    return {idp.title for idp in page.items}


# Search escaping


def test_idp_search_treats_percent_and_underscore_literally(make_idp):
    make_idp(title="Sale 100% off", description="")
    make_idp(title="Plain loft", description="")
    make_idp(title="a_b cottage", description="")
    make_idp(title="axb cottage", description="")
    assert titles(IDPEntity.searchIDPs("%", None, None, None, None, None)) == {"Sale 100% off"}
    assert titles(IDPEntity.searchIDPs("a_b", None, None, None, None, None)) == {"a_b cottage"}


def test_favourite_search_treats_percent_and_underscore_literally(make_account, make_idp):
    user = make_account()
    a = make_idp(title="Sale 100% off", description="")
    b = make_idp(title="Plain loft", description="")
    FavouriteEntity.saveFavourite(user.userId, a.idpId, "")
    FavouriteEntity.saveFavourite(user.userId, b.idpId, "my_note")
    assert [f.idpId for f in FavouriteEntity.searchFavourites(user.userId, "%")] == [a.idpId]
    assert [f.idpId for f in FavouriteEntity.searchFavourites(user.userId, "y_n")] == [b.idpId]
    assert FavouriteEntity.searchFavourites(user.userId, "yxn") == []


# Suspended or deleted designers are hidden everywhere public


@pytest.fixture(params=["suspended", "anonymised"])
def hidden_idp(request, make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer, title="Hidden loft", style="Japandi", isFeatured=True)
    if request.param == "suspended":
        designer.suspend()
    else:
        designer.isAnonymised = True
        db.session.commit()
    return idp


def test_hidden_designer_idp_is_not_public(hidden_idp, make_idp, make_account):
    assert titles(IDPEntity.getActiveIDPs()) == set()
    assert titles(IDPEntity.searchIDPs("loft", None, None, None, None, None)) == set()
    assert IDPEntity.recordView(hidden_idp.idpId, None) is None
    assert IDPEntity.getActiveByDesigner(hidden_idp.designerId) == []
    assert IDPEntity.compareIDPs([hidden_idp.idpId]) == []
    assert IDPEntity.getPopularIDPs() == []
    assert IDPEntity.getFeaturedIDPs() == []
    assert IDPEntity.countFeaturedIDPs() == 0


def test_hidden_designer_idp_is_not_recommended(hidden_idp, make_idp, make_account):
    user = make_account()
    seen = make_idp(style="Japandi", category=hidden_idp.category)
    FavouriteEntity.saveFavourite(user.userId, seen.idpId, "")
    assert not IDPEntity.getRecommendedIDPs(user.userId)


def test_details_page_of_a_suspended_designer_is_not_found(client, make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    designer.suspend()
    assert client.get(f"/idps/{idp.idpId}").status_code == 404


# Weekly stats count only Active IDPs


def test_weekly_stats_ignore_non_active_idps(make_account, make_idp):
    designer = make_account(role="designer")
    live = make_idp(designer=designer, title="Live")
    gone = make_idp(designer=designer, title="Gone", status="Removed")
    for idp in (live, gone):
        db.session.add(PlatformActivityEntity(activityType="view", idpId=idp.idpId))
    db.session.commit()
    stats = IDPEntity.getWeeklyStats(designer.userId)
    assert stats.totalViews == 1
    assert stats.topIDPs == [("Live", 1)]


# Favourite note length


def test_note_over_255_characters_is_rejected_by_the_entity(make_account, make_idp):
    user, idp = make_account(), make_idp()
    assert FavouriteEntity.saveFavourite(user.userId, idp.idpId, "x" * 256) is None
    assert FavouriteEntity.getFavourite(user.userId, idp.idpId) is None
    assert FavouriteEntity.saveFavourite(user.userId, idp.idpId, "x" * 255) is not None


# Registration activity in the account's own transaction


def test_create_account_can_record_the_register_activity_atomically(default_profiles):
    account = UserAccountEntity.createUserAccount(
        "newbie",
        "newbie@example.com",
        "Passw0rd!",
        "New Bie",
        default_profiles["customer"],
        recordRegistration=True,
    )
    rows = PlatformActivityEntity.query.filter_by(activityType="register").all()
    assert [r.userId for r in rows] == [account.userId]


def test_admin_created_account_records_a_register_activity(make_account, default_profiles):
    from app.control.create_user_account_controller import CreateUserAccountController

    admin = make_account(role="admin")
    account = CreateUserAccountController().createUserAccount(
        "madebyadmin", "m@example.com", "Passw0rd!", "Made", default_profiles["customer"].profileId,
        "", admin.userId,
    )
    rows = PlatformActivityEntity.query.filter_by(activityType="register").all()
    assert [r.userId for r in rows] == [account.userId]
