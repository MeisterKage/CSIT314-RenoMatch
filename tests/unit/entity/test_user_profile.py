import pytest

from app.entity import UserProfile


def test_create_profile_persists_fields(app):
    profile = UserProfile.create("Customer", "customer", "Homeowners looking for designers")
    found = UserProfile.find_by_name("Customer")
    assert found.id == profile.id
    assert found.role_type == "customer"
    assert found.description == "Homeowners looking for designers"
    assert found.is_suspended is False


def test_create_profile_rejects_unknown_role(app):
    with pytest.raises(ValueError):
        UserProfile.create("Hacker", "superuser")


def test_find_default_for_role_uses_default_names(default_profiles):
    assert UserProfile.find_default_for_role("designer").name == "Interior Designer"
    assert UserProfile.find_default_for_role("nobody") is None
