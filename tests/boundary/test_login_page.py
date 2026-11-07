import pytest

from app.entity import db
from tests.helpers import TEST_PASSWORD


@pytest.mark.parametrize(
    "role, home",
    [
        ("admin", "/admin/"),
        ("designer", "/"),
        ("customer", "/"),
        ("platform", "/platform/"),
    ],
)
def test_login_redirects_each_role_to_its_home(client, make_account, role, home):
    account = make_account(role=role)
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.status_code == 302
    assert resp.headers["Location"] == home


def test_login_page_renders_for_anonymous_visitor(client, default_profiles):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Log in" in resp.data


def test_login_page_shows_error_for_bad_password(client, make_account):
    account = make_account()
    resp = client.post("/login", data={"username": account.username, "password": "nope"})
    assert resp.status_code == 200
    assert b"Invalid username or password." in resp.data


def test_role_home_requires_login(client, default_profiles):
    resp = client.get("/customer/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_role_home_forbids_other_roles(client, make_account, login):
    login(make_account(role="customer").username)
    assert client.get("/admin/").status_code == 403


def test_account_suspended_mid_session_is_sent_to_login(client, make_account, login):
    account = make_account(role="customer")
    login(account.username)
    account.status = "Suspended"
    db.session.commit()
    assert client.get("/customer/").headers["Location"] == "/login"


def test_logged_in_user_visiting_login_goes_home(client, make_account, login):
    login(make_account(role="platform").username)
    assert client.get("/login").headers["Location"] == "/platform/"


def test_role_home_greets_user_by_name(client, make_account, login):
    login(make_account(role="admin", name="Dana Tan").username)
    assert b"Welcome, Dana Tan." in client.get("/admin/").data


def test_login_page_shows_the_locked_message_after_five_failures(client, make_account):
    account = make_account()
    for _ in range(5):
        client.post("/login", data={"username": account.username, "password": "nope"})
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.status_code == 200
    assert (
        b"This account is locked. Try again later or contact an administrator." in resp.data
    )
