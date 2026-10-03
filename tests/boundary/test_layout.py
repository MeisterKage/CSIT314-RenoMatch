import pytest


def test_site_stylesheet_is_served(client):
    resp = client.get("/static/site.css")
    assert resp.status_code == 200
    assert b"--shutter-teal" in resp.data


def test_pages_use_site_stylesheet_not_bootstrap(client):
    page = client.get("/").data
    assert b"/static/site.css" in page
    assert b"bootstrap" not in page


def test_pages_have_skip_link_to_main_content(client):
    page = client.get("/").data
    assert b'href="#main"' in page
    assert b'id="main"' in page


@pytest.mark.parametrize(
    "role, home, tool, status",
    [
        ("admin", "/admin/", b"User accounts", b"Coming in Sprint 1"),
        ("designer", "/designer/", b"Portfolio projects", b"Coming in Sprint 2"),
        ("customer", "/customer/", b"Search designs", b"Coming in Sprint 3"),
        ("platform", "/platform/", b"Activity reports", b"Coming in Sprint 3"),
    ],
)
def test_role_home_lists_its_tools_with_status(
    client, make_account, login, role, home, tool, status
):
    login(make_account(role=role).username)
    page = client.get(home).data
    assert tool in page
    assert status in page


def test_role_home_links_to_change_password_as_available(client, make_account, login):
    login(make_account(role="customer").username)
    page = client.get("/customer/").data
    assert b'href="/account/password"' in page
    assert b"Available" in page
