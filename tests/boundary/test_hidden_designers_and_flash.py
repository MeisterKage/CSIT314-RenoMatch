from app.entity import IDPEntity, db
from app.entity.favourite import FavouriteEntity
from tests.helpers import TEST_PASSWORD


def suspend_profile(idp):
    idp.designer.profile.status = "Suspended"
    db.session.commit()


def test_idp_is_hidden_when_the_designers_profile_is_suspended(client, make_idp):
    idp = make_idp()
    suspend_profile(idp)
    assert client.get(f"/idps/{idp.idpId}").status_code == 404
    assert client.get(f"/designers/{idp.designerId}").status_code == 404
    assert idp.title.encode() not in client.get("/idps").data


def test_hidden_idp_cannot_be_saved_or_enquired_about(client, make_account, make_idp, login):
    idp = make_idp()
    suspend_profile(idp)
    login(make_account().username)
    assert client.post(f"/idps/{idp.idpId}/favourite", data={"note": "x"}).status_code == 404
    resp = client.post(f"/idps/{idp.idpId}/enquiry", data={"subject": "s", "message": "m"})
    assert resp.status_code == 404


def test_hidden_idp_drops_out_of_favourites(client, make_account, make_idp, login):
    idp = make_idp()
    customer = make_account()
    FavouriteEntity.saveFavourite(customer.userId, idp.idpId, "")
    suspend_profile(idp)
    login(customer.username)
    assert idp.title.encode() not in client.get("/favourites").data


def test_featured_limit_counts_featured_idps_of_hidden_designers(make_idp):
    idp = make_idp(isFeatured=True)
    suspend_profile(idp)
    assert IDPEntity.countFeaturedIDPs() == 1


def test_my_idp_search_treats_percent_as_a_plain_character(make_account, make_idp):
    designer = make_account(role="designer")
    make_idp(designer=designer, title="Kitchen")
    assert IDPEntity.searchMyIDPs(designer.userId, "%") == []


def test_password_changed_message_appears_above_the_home_photo(client, make_account, login):
    account = make_account()
    login(account.username)
    page = client.post(
        "/account/password",
        data={
            "current_password": TEST_PASSWORD,
            "new_password": "N3wPassword",
            "confirm_password": "N3wPassword",
        },
        follow_redirects=True,
    ).data
    assert page.index(b"Password changed") < page.index(b'class="hero"')
