import pytest

from app.control.errors import LoginError
from app.control.login_controller import LoginController
from app.entity import db
from tests.helpers import TEST_PASSWORD


def test_login_returns_account_for_correct_credentials(make_account):
    account = make_account(username="alice")
    assert LoginController().login("alice", TEST_PASSWORD).id == account.id


def test_login_accepts_username_regardless_of_case(make_account):
    account = make_account(username="alice")
    assert LoginController().login("ALICE", TEST_PASSWORD).id == account.id


def test_login_rejects_wrong_password(make_account):
    make_account(username="alice")
    with pytest.raises(LoginError, match="Invalid username or password"):
        LoginController().login("alice", "wrong-password")


def test_login_rejects_unknown_username(default_profiles):
    with pytest.raises(LoginError, match="Invalid username or password"):
        LoginController().login("ghost", TEST_PASSWORD)


def test_login_rejects_suspended_account(make_account):
    account = make_account(username="alice")
    account.is_suspended = True
    db.session.commit()
    with pytest.raises(LoginError, match="suspended"):
        LoginController().login("alice", TEST_PASSWORD)


def test_login_rejects_account_whose_profile_is_suspended(make_account):
    account = make_account(username="alice")
    account.profile.is_suspended = True
    db.session.commit()
    with pytest.raises(LoginError, match="suspended"):
        LoginController().login("alice", TEST_PASSWORD)


def test_get_active_account_only_returns_accounts_that_may_log_in(make_account):
    account = make_account()
    controller = LoginController()
    assert controller.get_active_account(account.id).id == account.id
    account.is_suspended = True
    db.session.commit()
    assert controller.get_active_account(account.id) is None
    assert controller.get_active_account(99999) is None
