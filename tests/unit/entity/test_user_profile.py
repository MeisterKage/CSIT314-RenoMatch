import pytest

from app.entity import UserProfileEntity


def test_create_profile_persists_fields(app):
    profile = UserProfileEntity.createUserProfile(
        "Customer", "customer", "Homeowners looking for designers"
    )
    found = UserProfileEntity.findByName("Customer")
    assert found.profileId == profile.profileId
    assert found.roleType == "customer"
    assert found.description == "Homeowners looking for designers"
    assert found.status == "Active"


def test_create_profile_rejects_unknown_role(app):
    with pytest.raises(ValueError):
        UserProfileEntity.createUserProfile("Hacker", "superuser")


def test_find_default_for_role_uses_default_names(default_profiles):
    assert UserProfileEntity.findDefaultForRole("designer").name == "Interior Designer"
    assert UserProfileEntity.findDefaultForRole("nobody") is None
