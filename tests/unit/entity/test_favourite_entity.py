"""US-14, US-15, US-16, US-17: FavouriteEntity."""

from app.entity import FavouriteEntity, IDPEntity, PlatformActivityEntity, db


def shortlists(idpId):
    return PlatformActivityEntity.query.filter_by(activityType="shortlist", idpId=idpId).count()


def test_save_favourite_stores_row_activity_and_counter(make_idp, make_account):
    user, idp = make_account(), make_idp()
    favourite = FavouriteEntity.saveFavourite(user.userId, idp.idpId, "Love the sofa")
    assert favourite.note == "Love the sofa"
    assert favourite.userId == user.userId
    assert shortlists(idp.idpId) == 1
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1


def test_save_favourite_defaults_to_blank_note(make_idp, make_account):
    user, idp = make_account(), make_idp()
    assert FavouriteEntity.saveFavourite(user.userId, idp.idpId, None).note == ""


def test_saving_twice_updates_the_note_and_counts_once(make_idp, make_account):
    user, idp = make_account(), make_idp()
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "first")
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "second")
    assert FavouriteEntity.query.count() == 1
    assert FavouriteEntity.query.one().note == "second"
    assert shortlists(idp.idpId) == 1
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1


def test_save_favourite_rejects_missing_or_inactive_idp(make_idp, make_account):
    user = make_account()
    suspended = make_idp(status="Suspended")
    assert FavouriteEntity.saveFavourite(user.userId, suspended.idpId, "") is None
    assert FavouriteEntity.saveFavourite(user.userId, 9999, "") is None
    assert FavouriteEntity.query.count() == 0
    assert PlatformActivityEntity.query.count() == 0


def test_remove_favourite_keeps_counter_and_activity(make_idp, make_account):
    user, idp = make_account(), make_idp()
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "")
    assert FavouriteEntity.removeFavourite(user.userId, idp.idpId) is True
    assert FavouriteEntity.query.count() == 0
    assert shortlists(idp.idpId) == 1
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1


def test_remove_favourite_that_is_not_saved(make_idp, make_account):
    user, idp = make_account(), make_idp()
    assert FavouriteEntity.removeFavourite(user.userId, idp.idpId) is False


def test_remove_only_affects_that_user(make_idp, make_account):
    a, b, idp = make_account(), make_account(), make_idp()
    FavouriteEntity.saveFavourite(a.userId, idp.idpId, "")
    FavouriteEntity.saveFavourite(b.userId, idp.idpId, "")
    FavouriteEntity.removeFavourite(a.userId, idp.idpId)
    assert [f.userId for f in FavouriteEntity.query.all()] == [b.userId]


def test_get_favourites_lists_own_active_newest_first(make_idp, make_account):
    user, other = make_account(), make_account()
    first, second, hidden = make_idp(title="One"), make_idp(title="Two"), make_idp(title="Gone")
    for idp in (first, second, hidden):
        FavouriteEntity.saveFavourite(user.userId, idp.idpId, "")
    FavouriteEntity.saveFavourite(other.userId, first.idpId, "")
    hidden.status = "Removed"
    db.session.commit()
    found = FavouriteEntity.getFavourites(user.userId)
    assert [f.idp.title for f in found] == ["Two", "One"]


def test_search_favourites_matches_title_description_and_note(make_idp, make_account):
    user = make_account()
    by_title = make_idp(title="Japandi loft")
    by_description = make_idp(title="B", description="has a pergola")
    by_note = make_idp(title="C")
    make_idp(title="Unsaved japandi")
    miss = make_idp(title="D")
    FavouriteEntity.saveFavourite(user.userId, by_title.idpId, "")
    FavouriteEntity.saveFavourite(user.userId, by_description.idpId, "")
    FavouriteEntity.saveFavourite(user.userId, by_note.idpId, "ask about JAPANDI tiles")
    FavouriteEntity.saveFavourite(user.userId, miss.idpId, "")
    found = FavouriteEntity.searchFavourites(user.userId, "japandi")
    assert {f.idpId for f in found} == {by_title.idpId, by_note.idpId}
    found = FavouriteEntity.searchFavourites(user.userId, "pergola")
    assert [f.idpId for f in found] == [by_description.idpId]


def test_search_favourites_blank_keyword_lists_all(make_idp, make_account):
    user, idp = make_account(), make_idp()
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "")
    assert len(FavouriteEntity.searchFavourites(user.userId, "  ")) == 1
