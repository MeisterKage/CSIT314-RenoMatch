"""US-43 (diagrammed), US-44 and US-46 pages."""

from app.boundary.portfolio import MyIDPDetailsPage
from app.control.view_idp_view_count_controller import ViewIDPViewCountController


def test_details_page_holds_the_view_count_controller_as_controller(app):
    assert isinstance(MyIDPDetailsPage().controller, ViewIDPViewCountController)


def test_details_page_shows_views_and_shortlists(client, make_account, make_idp, login):
    designer = make_account(role="designer")
    idp = make_idp(designer, viewCount=12, shortlistCount=3)
    login(designer.username)
    page = client.get(f"/designer/portfolio/{idp.idpId}").data
    assert b"12 views" in page
    assert b"3 shortlists" in page


def test_details_page_shows_zero_views_when_not_viewed_yet(client, make_account, make_idp, login):
    designer = make_account(role="designer")
    idp = make_idp(designer)
    login(designer.username)
    page = client.get(f"/designer/portfolio/{idp.idpId}").data
    assert b"0 views" in page
    assert b"0 shortlists" in page


def test_details_page_calls_display_methods_per_alt_branch(
    app, client, make_account, make_idp, login, monkeypatch
):
    calls = []
    for name in ("displayViewCount", "displayNoViews"):
        function = getattr(MyIDPDetailsPage, name)

        def spy(self, function=function, name=name):
            calls.append(name)
            return function(self)

        monkeypatch.setattr(MyIDPDetailsPage, name, spy)
    designer = make_account(role="designer")
    viewed = make_idp(designer, viewCount=2)
    unseen = make_idp(designer)
    login(designer.username)
    client.get(f"/designer/portfolio/{viewed.idpId}")
    client.get(f"/designer/portfolio/{unseen.idpId}")
    assert calls == ["displayViewCount", "displayNoViews"]


def test_dashboard_shows_bars_and_top_idps(client, make_account, make_category, make_idp, login):
    designer = make_account(role="designer")
    kitchen = make_category(name="Kitchen")
    make_idp(designer, kitchen, title="Alpha loft", style="Modern", viewCount=10, shortlistCount=2)
    make_idp(designer, kitchen, title="Beta nook", style="Japandi", viewCount=4, shortlistCount=1)
    login(designer.username)
    response = client.get("/designer/dashboard")
    page = response.data
    assert response.status_code == 200
    assert b"Interest dashboard" in page
    assert b"Modern" in page and b"Japandi" in page and b"Kitchen" in page
    assert b"Alpha loft" in page and b"Beta nook" in page
    assert b"10 views" in page


def test_dashboard_empty_message(client, make_account, login):
    login(make_account(role="designer").username)
    assert b"No project interest yet" in client.get("/designer/dashboard").data


def test_dashboard_is_for_designers_only(client, make_account, login):
    assert client.get("/designer/dashboard").status_code == 302
    login(make_account(role="customer").username)
    assert client.get("/designer/dashboard").status_code == 403


def test_designer_home_links_the_interest_tools(client, make_account, login):
    login(make_account(role="designer").username)
    page = client.get("/designer/").data
    assert b'href="/designer/dashboard"' in page
    assert b'href="/designer/portfolio"' in page
    assert b"Coming in Sprint" not in page


def test_nav_has_a_dashboard_link_for_designers(client, make_account, login):
    login(make_account(role="designer").username)
    assert b'href="/designer/dashboard">Dashboard</a>' in client.get("/designer/").data
