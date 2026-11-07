from pathlib import Path

import pytest

from tests.helpers import TEST_PASSWORD

CSS = Path(__file__).parents[2] / "app" / "boundary" / "static" / "site.css"


def test_customer_lands_on_the_website_home_after_login(client, make_account):
    account = make_account(role="customer")
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.headers["Location"] == "/"


def test_old_customer_home_address_redirects_to_the_website_home(client, make_account, login):
    login(make_account(role="customer").username)
    resp = client.get("/customer/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_customer_home_page_has_no_link_to_a_separate_home(client, make_account, login):
    login(make_account(role="customer").username)
    page = client.get("/").data
    assert b"Go to your home" not in page
    assert b"Your home" not in page
    assert b"Recommended for you" in page or b"Popular designs" in page


@pytest.mark.parametrize("role, home", [("admin", "/admin/"), ("platform", "/platform/")])
def test_admin_and_manager_keep_their_own_home(client, make_account, role, home):
    account = make_account(role=role)
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.headers["Location"] == home


def test_designer_lands_on_the_website_home_after_login(client, make_account):
    account = make_account(role="designer")
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.headers["Location"] == "/"


def test_old_designer_home_address_redirects_to_the_website_home(client, make_account, login):
    login(make_account(role="designer").username)
    resp = client.get("/designer/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_designer_home_page_points_to_the_portfolio(client, make_account, login):
    login(make_account(role="designer").username)
    page = client.get("/").data
    assert b"Go to your home" not in page
    assert b"Your home" not in page
    assert b">Your portfolio</a>" in page


def test_designer_can_still_reach_every_former_home_tool(client, make_account, login):
    login(make_account(role="designer").username)
    page = client.get("/").data
    for path in (
        b"/designer/portfolio",
        b"/designer/dashboard",
        b"/designer/enquiries",
        b"/designer/company",
        b"/account",
    ):
        assert b'href="' + path in page
    account_page = client.get("/account").data
    assert b"Weekly summary" in account_page
    assert b'href="/account/password"' in account_page


def test_compare_needs_only_the_add_to_compare_button(client, make_account, make_idp, login):
    idp = make_idp()
    login(make_account(role="customer").username)
    page = client.get(f"/idps/{idp.idpId}").data
    assert b'type="checkbox"' not in page
    assert b"Add to compare" in page
    assert f'type="hidden" name="idpId" value="{idp.idpId}"'.encode() in page


def test_whole_tool_card_is_clickable():
    css = CSS.read_text(encoding="utf-8")
    assert ".tool h3 a::after" in css
