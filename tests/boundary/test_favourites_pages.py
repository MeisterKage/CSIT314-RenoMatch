"""US-14, US-15, US-16, US-17: save form, favourites page, remove and search."""

from app.entity import FavouriteEntity, IDPEntity, db


def customer_login(make_account, login, **fields):
    account = make_account(**fields)
    login(account.username)
    return account


def test_details_page_shows_save_form_to_customers_only(client, make_idp, make_account, login):
    idp = make_idp()
    assert f"/idps/{idp.idpId}/favourite".encode() not in client.get(f"/idps/{idp.idpId}").data
    customer_login(make_account, login)
    page = client.get(f"/idps/{idp.idpId}").data
    assert f"/idps/{idp.idpId}/favourite".encode() in page
    assert b'name="note"' in page


def test_details_form_prefills_saved_note(client, make_idp, make_account, login):
    idp = make_idp()
    user = customer_login(make_account, login)
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "Keep this one")
    page = client.get(f"/idps/{idp.idpId}").data
    assert b"Keep this one" in page


def test_save_favourite_post(client, make_idp, make_account, login):
    idp = make_idp()
    user = customer_login(make_account, login)
    resp = client.post(f"/idps/{idp.idpId}/favourite", data={"note": "Love it"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/idps/{idp.idpId}")
    assert FavouriteEntity.query.filter_by(userId=user.userId).one().note == "Love it"
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1


def test_save_twice_updates_note_without_recount(client, make_idp, make_account, login):
    idp = make_idp()
    customer_login(make_account, login)
    client.post(f"/idps/{idp.idpId}/favourite", data={"note": "one"})
    client.post(f"/idps/{idp.idpId}/favourite", data={"note": "two"})
    assert FavouriteEntity.query.one().note == "two"
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1


def test_save_without_note_is_allowed(client, make_idp, make_account, login):
    idp = make_idp()
    customer_login(make_account, login)
    assert client.post(f"/idps/{idp.idpId}/favourite").status_code == 302
    assert FavouriteEntity.query.one().note == ""


def test_save_rejects_overlong_note(client, make_idp, make_account, login):
    idp = make_idp()
    customer_login(make_account, login)
    resp = client.post(f"/idps/{idp.idpId}/favourite", data={"note": "x" * 300})
    assert resp.status_code == 302
    assert FavouriteEntity.query.count() == 0


def test_save_unknown_or_inactive_idp_is_404(client, make_idp, make_account, login):
    suspended = make_idp(status="Suspended")
    customer_login(make_account, login)
    assert client.post(f"/idps/{suspended.idpId}/favourite").status_code == 404
    assert client.post("/idps/9999/favourite").status_code == 404


def test_save_requires_login_and_customer_role(client, make_idp, make_account, login):
    idp = make_idp()
    resp = client.post(f"/idps/{idp.idpId}/favourite")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    for role in ("designer", "admin", "platform"):
        client.post("/logout")
        login(make_account(role=role).username)
        assert client.post(f"/idps/{idp.idpId}/favourite").status_code == 403
    assert FavouriteEntity.query.count() == 0


def test_favourites_page_shows_photo_cards_with_notes(client, make_idp, make_account, login):
    user = customer_login(make_account, login)
    idp = make_idp(title="Warm loft", photoUrls=["/static/img/idp/idp-01.jpg"])
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "Ask about the rug")
    page = client.get("/favourites").data
    assert b"Warm loft" in page
    assert b"/static/img/idp/idp-01.jpg" in page
    assert b"Ask about the rug" in page
    assert f"/favourites/{idp.idpId}/remove".encode() in page
    assert f"/idps/{idp.idpId}/favourite".encode() in page  # edit a note by saving again


def test_favourites_page_only_shows_own(client, make_idp, make_account, login):
    other = make_account()
    idp = make_idp(title="Not mine")
    FavouriteEntity.saveFavourite(other.userId, idp.idpId, "")
    customer_login(make_account, login)
    page = client.get("/favourites").data
    assert b"Not mine" not in page
    assert b"no favourites yet" in page


def test_edit_note_from_favourites_page_returns_there(client, make_idp, make_account, login):
    user = customer_login(make_account, login)
    idp = make_idp()
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "old")
    resp = client.post(
        f"/idps/{idp.idpId}/favourite", data={"note": "new", "next": "favourites"}
    )
    assert resp.headers["Location"].endswith("/favourites")
    assert FavouriteEntity.query.one().note == "new"


def test_remove_favourite(client, make_idp, make_account, login):
    user = customer_login(make_account, login)
    idp = make_idp(title="Short lived")
    FavouriteEntity.saveFavourite(user.userId, idp.idpId, "")
    resp = client.post(f"/favourites/{idp.idpId}/remove")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/favourites")
    assert FavouriteEntity.query.count() == 0
    assert db.session.get(IDPEntity, idp.idpId).shortlistCount == 1
    assert b"Short lived" not in client.get("/favourites").data


def test_remove_something_not_saved_still_redirects(client, make_idp, make_account, login):
    customer_login(make_account, login)
    idp = make_idp()
    assert client.post(f"/favourites/{idp.idpId}/remove").status_code == 302


def test_search_favourites(client, make_idp, make_account, login):
    user = customer_login(make_account, login)
    hit, miss = make_idp(title="Japandi nook"), make_idp(title="Industrial loft")
    FavouriteEntity.saveFavourite(user.userId, hit.idpId, "")
    FavouriteEntity.saveFavourite(user.userId, miss.idpId, "")
    page = client.get("/favourites?keyword=japandi").data
    assert b"Japandi nook" in page and b"Industrial loft" not in page
    assert b"No favourites match" in client.get("/favourites?keyword=zzz").data


def test_favourites_pages_are_customer_only(client, make_idp, make_account, login):
    resp = client.get("/favourites")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    idp = make_idp()
    for role in ("designer", "admin", "platform"):
        client.post("/logout")
        login(make_account(role=role).username)
        assert client.get("/favourites").status_code == 403
        assert client.post(f"/favourites/{idp.idpId}/remove").status_code == 403


def test_customer_nav_has_favourites_link(client, make_account, login):
    assert b'href="/favourites"' not in client.get("/").data
    customer_login(make_account, login)
    assert b'href="/favourites"' in client.get("/").data
    client.post("/logout")
    login(make_account(role="designer").username)
    assert b'href="/favourites"' not in client.get("/").data
