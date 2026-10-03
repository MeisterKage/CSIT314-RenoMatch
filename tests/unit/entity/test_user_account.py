from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import LoginAttempt, PasswordResetToken, UserAccount, db
from app.entity.db import utcnow


def test_password_is_hashed_not_stored(make_account):
    account = make_account(password="Secret123")
    assert account.password_hash != "Secret123"
    assert account.check_password("Secret123")
    assert not account.check_password("secret123")


def test_email_is_stored_lowercase_and_found_case_insensitively(make_account):
    account = make_account(email="Mixed@Example.COM")
    assert account.email == "mixed@example.com"
    assert UserAccount.find_by_email("MIXED@example.com").id == account.id


def test_username_is_stored_lowercase_and_found_case_insensitively(make_account):
    account = make_account(username="MixedCase")
    assert account.username == "mixedcase"
    assert UserAccount.find_by_username("MIXEDCASE").id == account.id


def test_role_comes_from_profile(make_account):
    assert make_account(role="designer").role == "designer"


def test_active_account_can_log_in(make_account):
    assert make_account().can_log_in()


def test_suspended_account_cannot_log_in(make_account):
    account = make_account()
    account.is_suspended = True
    assert not account.can_log_in()


def test_account_with_suspended_profile_cannot_log_in(make_account):
    account = make_account()
    account.profile.is_suspended = True
    assert not account.can_log_in()


def test_anonymised_account_cannot_log_in(make_account):
    account = make_account()
    account.is_anonymised = True
    assert not account.can_log_in()


def test_change_password_replaces_hash(make_account):
    account = make_account(password="OldPass123")
    account.change_password("NewPass456")
    db.session.expire_all()
    reloaded = UserAccount.find_by_id(account.id)
    assert reloaded.check_password("NewPass456")
    assert not reloaded.check_password("OldPass123")


def test_username_must_be_unique(make_account):
    make_account(username="alice")
    with pytest.raises(IntegrityError):
        make_account(username="alice")


def test_login_attempt_allows_unknown_username(app):
    attempt = LoginAttempt(username="ghost", account_id=None, success=False)
    db.session.add(attempt)
    db.session.commit()
    assert attempt.attempted_at is not None


def test_reset_token_hash_is_unique(make_account):
    account = make_account()
    expires = utcnow() + timedelta(hours=1)
    db.session.add(PasswordResetToken(account_id=account.id, token_hash="abc", expires_at=expires))
    db.session.commit()
    db.session.add(PasswordResetToken(account_id=account.id, token_hash="abc", expires_at=expires))
    with pytest.raises(IntegrityError):
        db.session.commit()
