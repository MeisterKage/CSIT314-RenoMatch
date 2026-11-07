from pathlib import Path

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


def test_other_roles_keep_their_own_home(client, make_account):
    account = make_account(role="designer")
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.headers["Location"] == "/designer/"


def test_whole_tool_card_is_clickable():
    css = CSS.read_text(encoding="utf-8")
    assert ".tool h3 a::after" in css
