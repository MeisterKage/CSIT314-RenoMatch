import pytest

from app.control.change_password_controller import ChangePasswordController
from app.control.errors import ValidationError
from tests.helpers import TEST_PASSWORD


def change(account, current=TEST_PASSWORD, new="N3wPassword", confirm="N3wPassword"):
    ChangePasswordController().change_password(account.userId, current, new, confirm)


def test_change_password_updates_the_hash(make_account):
    account = make_account()
    change(account)
    assert account.checkPassword("N3wPassword")
    assert not account.checkPassword(TEST_PASSWORD)


def test_rejects_wrong_current_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), current="wrong-password")
    assert exc.value.errors["current_password"] == "Current password is incorrect."


def test_rejects_weak_new_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), new="short", confirm="short")
    assert "new_password" in exc.value.errors


def test_rejects_reusing_the_current_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), new=TEST_PASSWORD, confirm=TEST_PASSWORD)
    assert exc.value.errors["new_password"] == (
        "New password must be different from the current one."
    )


def test_rejects_mismatched_confirmation(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), confirm="Different1")
    assert exc.value.errors["confirm_password"] == "Passwords do not match."


def test_failed_change_keeps_the_old_password(make_account):
    account = make_account()
    with pytest.raises(ValidationError):
        change(account, current="wrong-password")
    assert account.checkPassword(TEST_PASSWORD)


def test_unknown_account_raises_lookup_error(app):
    with pytest.raises(LookupError):
        ChangePasswordController().change_password(99999, "a", "b", "c")
