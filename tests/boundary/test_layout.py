import pytest


def test_site_stylesheet_is_served(client):
    with client.get("/static/site.css") as resp:
        assert resp.status_code == 200
        assert b"--charcoal" in resp.data


def test_pages_use_site_stylesheet_not_bootstrap(client):
    page = client.get("/").data
    assert b"/static/site.css" in page
    assert b"bootstrap" not in page


def test_home_page_shows_hero_photo_and_style_gallery(client):
    page = client.get("/").data
    assert b"img/hero-living.jpg" in page
    assert b"Browse by style" in page
    for style in (b"Japandi", b"Contemporary", b"Mid-Century", b"Industrial", b"Luxury"):
        assert style in page
    assert b"How it works" in page


def test_home_page_photos_are_served(client):
    with client.get("/static/img/hero-living.jpg") as resp:
        assert resp.status_code == 200
        assert resp.mimetype == "image/jpeg"


def test_pages_have_skip_link_to_main_content(client):
    page = client.get("/").data
    assert b'href="#main"' in page
    assert b'id="main"' in page


@pytest.mark.parametrize(
    "role, home, tools",
    [
        ("admin", "/admin/", [b"Failed logins", b"Export accounts", b"Audit log"]),
        ("platform", "/platform/", [b"Featured projects", b"Activity reports"]),
    ],
)
def test_role_home_lists_every_tool_as_a_link(client, make_account, login, role, home, tools):
    login(make_account(role=role).username)
    page = client.get(home).data
    assert b"Coming" not in page and b"sprint" not in page.lower()
    for tool in tools:
        assert tool in page
    assert b"Available" not in page


def test_role_home_links_to_change_password(client, make_account, login):
    login(make_account(role="admin").username)
    page = client.get("/admin/").data
    assert b'href="/account/password"' in page
