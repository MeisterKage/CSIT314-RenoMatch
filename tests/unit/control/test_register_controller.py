import pytest

from app.control.errors import ValidationError
from app.control.register_controller import RegisterController
from app.entity import db

VALID = {
    "username": "newuser",
    "email": "new@example.com",
    "password": "Passw0rd!",
    "confirm_password": "Passw0rd!",
    "full_name": "New User",
    "phone": "+65 9123 4567",
}


def register(**overrides):
    return RegisterController().register(**{**VALID, "role": "customer", **overrides})


def test_register_customer_uses_default_customer_profile(default_profiles):
    account = register()
    assert account.profile.name == "Customer"
    assert account.check_password("Passw0rd!")


def test_register_designer_uses_default_designer_profile(default_profiles):
    assert register(role="designer").profile.name == "Interior Designer"


def test_register_rejects_admin_role(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(role="admin")
    assert "role" in exc.value.errors


def test_register_rejects_taken_username(make_account):
    make_account(username="newuser")
    with pytest.raises(ValidationError) as exc:
        register()
    assert exc.value.errors["username"] == "That username is taken."


def test_register_rejects_taken_email_case_insensitively(make_account):
    make_account(email="NEW@example.com")
    with pytest.raises(ValidationError) as exc:
        register()
    assert exc.value.errors["email"] == "An account with that email already exists."


def test_register_rejects_mismatched_confirmation(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(confirm_password="Different1")
    assert exc.value.errors["confirm_password"] == "Passwords do not match."


def test_register_reports_every_problem_at_once(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(
            username="x", email="bad", password="short", confirm_password="short", full_name=""
        )
    assert {"username", "email", "password", "full_name"} <= set(exc.value.errors)


def test_register_is_closed_when_default_profile_is_suspended(default_profiles):
    default_profiles["designer"].is_suspended = True
    db.session.commit()
    with pytest.raises(ValidationError) as exc:
        register(role="designer")
    assert exc.value.errors["role"] == "Registration for this role is currently closed."
