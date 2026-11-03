"""US-05 reset password: every branch of the sequence diagram, through the pages."""

import logging
import re
from datetime import timedelta

import pytest

from app.entity import UserAccountEntity, db
from app.entity.db import utcnow
from tests.helpers import TEST_PASSWORD

SAME_MESSAGE = b"If that email is registered, we have sent a reset link."
LINK = re.compile(r"/reset-password/[\w-]+")


@pytest.fixture
def sent(caplog):
    """Logged emails (log mode), so a test can read the reset link."""
    caplog.set_level(logging.INFO, logger="app.boundary.email_service")
    return caplog


def link_from(caplog):
    found = LINK.findall(caplog.text)
    assert found, "no reset link was logged"
    return found[-1]


def request_link(client, email):
    return client.post("/forgot-password", data={"email": email})


def reset(client, link, password="N3wPassword", confirm=None):
    confirm = password if confirm is None else confirm
    return client.post(link, data={"newPassword": password, "confirmPassword": confirm})


def test_forgot_password_form_renders_and_login_links_to_it(client, default_profiles):
    assert b"Send Reset Link" in client.get("/forgot-password").data
    assert b"/forgot-password" in client.get("/login").data


def test_registered_email_logs_a_link_and_shows_the_message(client, make_account, sent):
    account = make_account()
    resp = request_link(client, account.email)
    assert resp.status_code == 200
    assert SAME_MESSAGE in resp.data
    assert account.email in sent.text
    assert LINK.search(sent.text)


def test_token_is_stored_hashed_and_expires_in_an_hour(client, make_account, sent):
    account = make_account()
    request_link(client, account.email)
    token = link_from(sent).rsplit("/", 1)[1]
    db.session.refresh(account)
    assert account.resetToken and account.resetToken != token
    assert timedelta(minutes=59) < account.tokenExpiry - utcnow() <= timedelta(hours=1)


def test_unknown_email_sends_nothing_but_shows_the_same_message(client, make_account, sent):
    make_account()
    resp = request_link(client, "nobody@example.com")
    assert SAME_MESSAGE in resp.data
    assert "nobody@example.com" not in sent.text
    assert not LINK.search(sent.text)


def test_reset_form_renders(client, make_account, sent):
    request_link(client, make_account().email)
    resp = client.get(link_from(sent))
    assert resp.status_code == 200
    assert b"newPassword" in resp.data


def test_successful_reset_changes_the_password(client, make_account, login, sent):
    account = make_account()
    request_link(client, account.email)
    resp = reset(client, link_from(sent))
    assert b"password has been reset" in resp.data
    assert login(account.username, "N3wPassword").status_code == 302
    client.post("/logout")
    assert login(account.username, TEST_PASSWORD).status_code == 200  # old password rejected


def test_token_is_single_use(client, make_account, sent):
    request_link(client, make_account().email)
    link = link_from(sent)
    assert b"password has been reset" in reset(client, link).data
    again = reset(client, link, "An0therPass")
    assert b"password has been reset" not in again.data
    assert b"invalid or has expired" in again.data


def test_expired_token_is_rejected(client, make_account, login, sent):
    account = make_account()
    request_link(client, account.email)
    account.tokenExpiry = utcnow() - timedelta(minutes=1)
    db.session.commit()
    resp = reset(client, link_from(sent))
    assert b"invalid or has expired" in resp.data
    assert login(account.username, TEST_PASSWORD).status_code == 302


def test_unknown_token_is_rejected(client, default_profiles):
    resp = reset(client, "/reset-password/not-a-real-token")
    assert b"invalid or has expired" in resp.data


@pytest.mark.parametrize("password", ["short1", "allletters", "12345678"])
def test_password_breaking_rules_is_rejected_and_token_kept(
    client, make_account, login, sent, password
):
    account = make_account()
    request_link(client, account.email)
    link = link_from(sent)
    resp = reset(client, link, password)
    assert b"at least 8 characters" in resp.data
    assert login(account.username, TEST_PASSWORD).status_code == 302
    client.post("/logout")
    assert b"password has been reset" in reset(client, link).data  # token still usable


def test_mismatched_confirmation_is_rejected(client, make_account, login, sent):
    account = make_account()
    request_link(client, account.email)
    resp = reset(client, link_from(sent), "N3wPassword", "Different1")
    assert b"do not match" in resp.data
    assert login(account.username, TEST_PASSWORD).status_code == 302


def test_new_request_replaces_the_old_token(client, make_account, sent):
    account = make_account()
    request_link(client, account.email)
    first = link_from(sent)
    request_link(client, account.email)
    second = link_from(sent)
    assert first != second
    assert b"invalid or has expired" in reset(client, first).data
    assert b"password has been reset" in reset(client, second).data


def test_lookup_is_case_insensitive(client, make_account, sent):
    account = make_account()
    request_link(client, account.email.upper())
    assert LINK.search(sent.text)
    assert UserAccountEntity.findByEmail(account.email).resetToken
