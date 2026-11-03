import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import LoginAttemptEntity, UserAccountEntity, db


def test_password_is_hashed_not_stored(make_account):
    account = make_account(password="Secret123")
    assert account.passwordHash != "Secret123"
    assert account.checkPassword("Secret123")
    assert not account.checkPassword("secret123")


def test_email_is_stored_lowercase_and_found_case_insensitively(make_account):
    account = make_account(email="Mixed@Example.COM")
    assert account.email == "mixed@example.com"
    assert UserAccountEntity.findByEmail("MIXED@example.com").userId == account.userId


def test_username_is_stored_lowercase_and_found_case_insensitively(make_account):
    account = make_account(username="MixedCase")
    assert account.username == "mixedcase"
    assert UserAccountEntity.findByUsername("MIXEDCASE").userId == account.userId


def test_find_by_id(make_account):
    account = make_account()
    assert UserAccountEntity.findById(account.userId) is account
    assert UserAccountEntity.findById(99999) is None


def test_role_comes_from_profile(make_account):
    account = make_account(role="designer")
    assert account.role == "designer"
    assert account.profileId == account.profile.profileId


def test_active_account_can_log_in(make_account):
    assert make_account().canLogIn()


def test_anonymised_account_cannot_log_in(make_account):
    account = make_account()
    account.isAnonymised = True
    assert not account.canLogIn()


def test_change_password_replaces_hash(make_account):
    account = make_account(password="OldPass123")
    account.changePassword("NewPass456")
    db.session.expire_all()
    reloaded = UserAccountEntity.findById(account.userId)
    assert reloaded.checkPassword("NewPass456")
    assert not reloaded.checkPassword("OldPass123")


def test_username_must_be_unique(make_account):
    make_account(username="alice")
    with pytest.raises(IntegrityError):
        make_account(username="alice")


def test_login_attempt_allows_unknown_username(app):
    attempt = LoginAttemptEntity(username="ghost", userId=None, success=False)
    db.session.add(attempt)
    db.session.commit()
    assert attempt.attemptedAt is not None


def test_reset_token_is_unique(make_account):
    first, second = make_account(), make_account()
    first.resetToken = second.resetToken = "hashed-token"
    with pytest.raises(IntegrityError):
        db.session.commit()
