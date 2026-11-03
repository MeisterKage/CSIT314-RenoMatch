"""US-07 update own details (and the designer weekly-summary opt-in) and US-08 delete account."""

import pytest

from app.entity import ReviewEntity, UserAccountEntity, db
from tests.helpers import TEST_PASSWORD


@pytest.mark.parametrize("role", ["admin", "designer", "customer", "platform"])
def test_my_account_page_serves_every_role(client, make_account, login, role):
    account = make_account(role=role)
    login(account.username)
    resp = client.get("/account")
    assert resp.status_code == 200
    assert account.email.encode() in resp.data
    assert b"/account/password" in resp.data
    assert b"Delete account" in resp.data
    assert (b"weekly" in resp.data.lower()) == (role == "designer")


def test_my_account_requires_login(client, default_profiles):
    assert client.get("/account").headers["Location"] == "/login"
    assert client.post("/account/delete").headers["Location"] == "/login"


def test_nav_has_an_account_link(client, make_account, login):
    login(make_account().username)
    assert b'href="/account"' in client.get("/customer/").data


def test_update_details(client, make_account, login):
    account = make_account()
    login(account.username)
    resp = client.post(
        "/account", data={"name": "New Name", "email": "New@Example.com", "phone": "91234567"}
    )
    assert resp.status_code == 200
    assert b"Your details have been updated" in resp.data
    db.session.refresh(account)
    assert (account.name, account.email, account.phone) == (
        "New Name",
        "new@example.com",
        "91234567",
    )


@pytest.mark.parametrize(
    "data, message",
    [
        ({"name": "", "email": "a@b.co", "phone": ""}, b"Enter your full name."),
        ({"name": "X", "email": "nope", "phone": ""}, b"Enter a valid email address."),
        ({"name": "X", "email": "a@b.co", "phone": "12"}, b"Phone number must be"),
    ],
)
def test_update_details_validates(client, make_account, login, data, message):
    account = make_account()
    login(account.username)
    original = account.name
    resp = client.post("/account", data=data)
    assert message in resp.data
    db.session.refresh(account)
    assert account.name == original


def test_update_details_rejects_a_taken_email_but_allows_own(client, make_account, login):
    other = make_account()
    account = make_account()
    login(account.username)
    taken = client.post("/account", data={"name": "X", "email": other.email, "phone": ""})
    assert b"already exists" in taken.data
    own = client.post("/account", data={"name": "X", "email": account.email, "phone": ""})
    assert b"Your details have been updated" in own.data


def test_designer_can_turn_weekly_summary_off_and_on(client, make_account, login):
    designer = make_account(role="designer")
    login(designer.username)
    assert designer.weeklySummaryOptIn is True
    client.post("/account/weekly-summary", data={})
    db.session.refresh(designer)
    assert designer.weeklySummaryOptIn is False
    client.post("/account/weekly-summary", data={"optIn": "on"})
    db.session.refresh(designer)
    assert designer.weeklySummaryOptIn is True


def test_customer_cannot_set_weekly_summary(client, make_account, login):
    login(make_account().username)
    assert client.post("/account/weekly-summary", data={"optIn": "on"}).status_code == 403


def delete(client, account, confirm=None, password=TEST_PASSWORD):
    return client.post(
        "/account/delete",
        data={"confirmUsername": confirm or account.username, "password": password},
    )


def test_delete_anonymises_logs_out_and_blocks_login(client, make_account, login):
    account = make_account(phone="91234567")
    username, userId = account.username, account.userId
    login(username)
    resp = delete(client, account)
    assert resp.headers["Location"] == "/"
    assert client.get("/account").headers["Location"] == "/login"
    db.session.refresh(account)
    assert account.isAnonymised is True
    assert account.name == "Deleted user"
    assert account.phone == ""
    assert username not in (account.username, account.email)
    assert account.userId == userId
    assert login(username).status_code == 200
    assert UserAccountEntity.findByUsername(username) is None


def test_delete_needs_the_username_and_password(client, make_account, login):
    account = make_account()
    login(account.username)
    assert b"type your username" in delete(client, account, confirm="wrong").data.lower()
    assert b"password is incorrect" in delete(client, account, password="bad").data
    db.session.refresh(account)
    assert account.isAnonymised is False


def test_deleted_users_reviews_stay_and_show_deleted_user(client, make_account, login):
    designer = make_account(role="designer")
    customer = make_account()
    db.session.add(
        ReviewEntity(designerId=designer.userId, userId=customer.userId, rating=4, comment="Good")
    )
    db.session.commit()
    login(customer.username)
    delete(client, customer)
    client.post("/logout")
    page = client.get(f"/designers/{designer.userId}")
    assert b"Deleted user" in page.data
    assert ReviewEntity.query.count() == 1
