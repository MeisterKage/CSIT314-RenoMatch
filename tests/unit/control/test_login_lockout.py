from datetime import timedelta

import pytest

from app.control.errors import LoginError
from app.control.login_controller import LoginController
from app.entity import LoginAttemptEntity, db
from app.entity.db import utcnow
from tests.helpers import TEST_PASSWORD

LOCKED = "This account is locked. Try again later or contact an administrator."


def fail(username, times):
    for _ in range(times):
        with pytest.raises(LoginError):
            LoginController().login(username, "wrong-password")


def test_four_failures_do_not_lock(make_account):
    account = make_account(username="alice")
    fail("alice", 4)
    assert account.failedLogins == 4
    assert account.lockedUntil is None
    assert LoginController().login("alice", TEST_PASSWORD).userId == account.userId


def test_fifth_failure_locks_for_fifteen_minutes(make_account):
    account = make_account(username="alice")
    fail("alice", 5)
    assert account.isLocked()
    expected = utcnow() + timedelta(minutes=15)
    assert abs((account.lockedUntil - expected).total_seconds()) < 5


def test_locked_account_shows_the_locked_message_even_with_the_right_password(make_account):
    make_account(username="alice")
    fail("alice", 5)
    with pytest.raises(LoginError) as error:
        LoginController().login("alice", TEST_PASSWORD)
    assert str(error.value) == LOCKED


def test_fifth_failure_already_shows_the_locked_message(make_account):
    make_account(username="alice")
    fail("alice", 4)
    with pytest.raises(LoginError) as error:
        LoginController().login("alice", "wrong-password")
    assert str(error.value) == LOCKED


def test_successful_login_resets_the_failed_count(make_account):
    account = make_account(username="alice")
    fail("alice", 3)
    LoginController().login("alice", TEST_PASSWORD)
    assert account.failedLogins == 0
    fail("alice", 4)
    assert not account.isLocked()


def test_lock_expires_after_fifteen_minutes(make_account):
    account = make_account(username="alice")
    fail("alice", 5)
    account.lockedUntil = utcnow() - timedelta(seconds=1)
    db.session.commit()
    assert LoginController().login("alice", TEST_PASSWORD).userId == account.userId
    assert account.lockedUntil is None


def test_a_failure_after_an_expired_lock_starts_a_new_count(make_account):
    account = make_account(username="alice")
    fail("alice", 5)
    account.lockedUntil = utcnow() - timedelta(seconds=1)
    db.session.commit()
    fail("alice", 1)
    assert account.failedLogins == 1
    assert not account.isLocked()


def test_unknown_username_is_recorded_without_an_account(default_profiles):
    fail("ghost", 1)
    attempt = LoginAttemptEntity.query.one()
    assert (attempt.username, attempt.userId, attempt.success) == ("ghost", None, False)


def test_attempts_are_recorded_for_failures_lock_and_success(make_account):
    account = make_account(username="alice")
    fail("alice", 5)
    with pytest.raises(LoginError):
        LoginController().login("alice", TEST_PASSWORD)
    attempts = LoginAttemptEntity.query.filter_by(userId=account.userId).all()
    assert len(attempts) == 6
    assert not any(attempt.success for attempt in attempts)
    account.lockedUntil = None
    db.session.commit()
    LoginController().login("alice", TEST_PASSWORD)
    assert LoginAttemptEntity.query.filter_by(userId=account.userId, success=True).count() == 1


def test_suspended_account_with_right_password_keeps_its_message(make_account):
    account = make_account(username="alice")
    account.status = "Suspended"
    db.session.commit()
    with pytest.raises(LoginError, match="suspended"):
        LoginController().login("alice", TEST_PASSWORD)
