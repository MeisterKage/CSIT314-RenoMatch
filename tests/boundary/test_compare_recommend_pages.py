"""US-12 home page recommendations and US-13 compare page."""

from app.boundary.public import HomePage
from app.entity import FavouriteEntity, PlatformActivityEntity, db


def customer(make_account, login):
    account = make_account()
    login(account.username)
    return account


def select(client, *idps):
    for idp in idps:
        client.post("/compare/select", data={"idpId": idp.idpId})


def view(user, idp):
    db.session.add(PlatformActivityEntity(activityType="view", userId=user.userId, idpId=idp.idpId))
    db.session.commit()


# US-13 step 1 and opt 1a


def test_select_adds_to_the_session_and_redirects(client, make_idp):
    a = make_idp()
    resp = client.post("/compare/select", data={"idpId": a.idpId})
    assert resp.status_code == 302
    with client.session_transaction() as session:
        assert session["compareIds"] == [a.idpId]


def test_select_same_idp_twice_keeps_one(client, make_idp):
    a = make_idp()
    select(client, a, a)
    with client.session_transaction() as session:
        assert session["compareIds"] == [a.idpId]


def test_fourth_selection_is_refused_with_the_1a_message(client, make_idp):
    idps = [make_idp() for _ in range(4)]
    select(client, *idps[:3])
    resp = client.post("/compare/select", data={"idpId": idps[3].idpId}, follow_redirects=True)
    assert b"You can compare up to 3 IDPs" in resp.data
    with client.session_transaction() as session:
        assert session["compareIds"] == [i.idpId for i in idps[:3]]


def test_reticking_a_selected_idp_at_the_limit_is_not_refused(client, make_idp):
    idps = [make_idp() for _ in range(3)]
    select(client, *idps)
    resp = client.post("/compare/select", data={"idpId": idps[0].idpId}, follow_redirects=True)
    assert b"up to 3" not in resp.data


def test_clear_empties_the_selection(client, make_idp):
    select(client, make_idp())
    assert client.post("/compare/clear").status_code == 302
    with client.session_transaction() as session:
        assert session.get("compareIds", []) == []


# US-13 step 2 alt branches


def test_two_selected_shows_the_table_with_every_row(client, make_idp, make_category):
    a = make_idp(title="Alpha", style="Japandi", location="Bishan", budget=30000.0)
    b = make_idp(
        title="Beta", style="Luxury", propertyType="Landed", category=make_category(name="Kitchens")
    )
    select(client, a, b)
    page = client.get("/compare").data.decode()
    for text in ("Alpha", "Beta", "Japandi", "Luxury", "Bishan", "Landed", "Kitchens",
                 "S$30,000", a.designer.name):
        assert text in page
    for label in ("Style", "Budget", "Location", "Property type", "Category", "Designer"):
        assert label in page
    assert page.count("View Details") == 2
    assert f"/idps/{a.idpId}" in page


def test_three_selected_shows_three_columns(client, make_idp):
    select(client, *[make_idp() for _ in range(3)])
    assert client.get("/compare").data.decode().count("View Details") == 3


def test_fewer_than_two_shows_the_2a_message_and_no_table(client, make_idp):
    a = make_idp()
    assert b"Select at least 2 IDPs to compare" in client.get("/compare").data
    select(client, a)
    page = client.get("/compare").data
    assert b"Select at least 2 IDPs to compare" in page
    assert b"View Details" not in page


def test_unavailable_idp_shows_the_rest_and_the_3a_message(client, make_idp):
    a, b, c = make_idp(title="Alpha"), make_idp(title="Beta"), make_idp(title="Gamma")
    select(client, a, b, c)
    b.status = "Suspended"
    db.session.commit()
    page = client.get("/compare").data.decode()
    assert "One IDP is no longer available" in page
    assert "Alpha" in page and "Gamma" in page and "Beta" not in page


def test_nav_shows_compare_count_for_customers(client, make_idp, make_account, login):
    customer(make_account, login)
    assert "Compare (0)" in client.get("/compare").data.decode()
    select(client, make_idp(), make_idp())
    assert "Compare (2)" in client.get("/compare").data.decode()


# US-12


def test_visitor_sees_featured_designs(client, make_idp):
    make_idp(title="Showcase Home", isFeatured=True)
    page = client.get("/").data
    assert b"Featured Designs" in page and b"Showcase Home" in page
    assert b"Recommended for you" not in page


def test_customer_with_matches_sees_recommended_above_styles(
    client, make_idp, make_account, make_category, login
):
    user = customer(make_account, login)
    cat = make_category()
    view(user, make_idp(category=cat, title="Seen One"))
    make_idp(category=cat, title="Suggested One")
    page = client.get("/").data.decode()
    assert "Recommended for you" in page and "Suggested One" in page
    assert page.index("Recommended for you") < page.index('id="styles"')
    assert "Featured Designs" not in page


def test_saved_idps_are_not_recommended(client, make_idp, make_account, make_category, login):
    user = customer(make_account, login)
    cat = make_category()
    saved = make_idp(category=cat, title="Already Saved")
    FavouriteEntity.saveFavourite(user.userId, saved.idpId, "")
    make_idp(category=cat, title="Fresh One")
    page = client.get("/").data.decode()
    assert "Fresh One" in page and "Already Saved" not in page


def test_customer_without_history_sees_popular_designs(client, make_idp, make_account, login):
    customer(make_account, login)
    make_idp(title="Crowd Favourite", viewCount=50)
    page = client.get("/").data.decode()
    assert "Popular designs" in page and "Crowd Favourite" in page
    assert "Recommended for you" not in page


def test_customer_with_history_but_no_matches_sees_the_message(
    client, make_idp, make_account, make_category, login
):
    user = customer(make_account, login)
    view(user, make_idp(style="Modern", category=make_category()))
    make_idp(style="Luxury", category=make_category(), title="Unrelated")
    page = client.get("/").data.decode()
    assert "No recommendations yet. Browse IDPs to get personalised suggestions" in page
    assert "Unrelated" not in page


def test_designer_home_shows_featured_not_recommendations(client, make_account, make_idp, login):
    login(make_account(role="designer").username)
    make_idp(isFeatured=True)
    page = client.get("/").data
    assert b"Featured Designs" in page and b"Recommended for you" not in page


def test_home_page_matches_the_class_diagram():
    page = HomePage()
    assert page.controller.__class__.__name__ == "ViewRecommendedIDPsController"
    for name in ("displayRecommendedIDPs", "displayPopularIDPs", "displayMessage"):
        assert callable(getattr(page, name))
