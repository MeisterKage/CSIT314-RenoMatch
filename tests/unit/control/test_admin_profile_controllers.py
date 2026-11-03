import pytest

from app.control.create_user_profile_controller import CreateUserProfileController
from app.control.errors import ValidationError
from app.control.reactivate_user_profile_controller import ReactivateUserProfileController
from app.control.search_user_profiles_controller import SearchUserProfilesController
from app.control.suspend_user_profile_controller import SuspendUserProfileController
from app.control.update_user_profile_controller import UpdateUserProfileController
from app.control.view_user_profile_controller import ViewUserProfileController
from app.entity import AuditLogEntity, UserProfileEntity


@pytest.fixture
def admin(make_account):
    return make_account(role="admin", username="boss")


def audit_rows():
    return AuditLogEntity.query.order_by(AuditLogEntity.logId).all()


def create(admin, name="Support Staff", description="Helps users", roleType="customer"):
    return CreateUserProfileController().createUserProfile(
        name, description, roleType, admin.userId
    )


# US-26 create


def test_create_profile_writes_audit_row(admin):
    profile = create(admin)
    assert profile.name == "Support Staff"
    assert profile.roleType == "customer"
    assert profile.status == "Active"
    (row,) = audit_rows()
    assert (row.action, row.targetType, row.targetId) == (
        "create_profile",
        "user_profile",
        profile.profileId,
    )
    assert row.adminId == admin.userId


@pytest.mark.parametrize(
    "name, roleType, field",
    [
        ("", "customer", "name"),
        ("x" * 61, "customer", "name"),
        ("Customer", "customer", "name"),
        ("customer", "customer", "name"),
        ("Fine", "wizard", "roleType"),
        ("Fine", "", "roleType"),
    ],
)
def test_create_profile_rejects_bad_input(admin, name, roleType, field):
    with pytest.raises(ValidationError) as error:
        create(admin, name=name, roleType=roleType)
    assert field in error.value.errors
    assert audit_rows() == []


def test_create_profile_rejects_long_description(admin):
    with pytest.raises(ValidationError) as error:
        create(admin, description="x" * 256)
    assert "description" in error.value.errors


# US-27 view


def test_view_profile_and_account_count(admin, make_account):
    make_account(role="customer")
    make_account(role="customer")
    customer = UserProfileEntity.findByName("Customer")
    found = ViewUserProfileController().getUserProfile(customer.profileId)
    assert found.roleType == "customer"
    assert found.accountCount == 2
    assert ViewUserProfileController().getUserProfile(9999) is None


# US-28 update


def test_update_profile_name_and_description(admin):
    profile = create(admin)
    UpdateUserProfileController().updateUserProfile(
        profile.profileId, "Support Team", "New text", admin.userId
    )
    assert (profile.name, profile.description) == ("Support Team", "New text")
    assert audit_rows()[-1].action == "update_profile"
    assert audit_rows()[-1].targetType == "user_profile"


def test_update_profile_can_keep_its_own_name(admin):
    profile = create(admin)
    UpdateUserProfileController().updateUserProfile(
        profile.profileId, "Support Staff", "Changed", admin.userId
    )
    assert profile.description == "Changed"


def test_update_profile_rejects_taken_name_and_missing_profile(admin):
    profile = create(admin)
    with pytest.raises(ValidationError) as error:
        UpdateUserProfileController().updateUserProfile(
            profile.profileId, "customer", "", admin.userId
        )
    assert "name" in error.value.errors
    with pytest.raises(ValidationError) as error:
        UpdateUserProfileController().updateUserProfile(9999, "Name", "", admin.userId)
    assert "profile" in error.value.errors


# US-29 and US-30 suspend and reactivate


def test_suspend_and_reactivate_profile(admin):
    profile = create(admin)
    SuspendUserProfileController().suspendUserProfile(profile.profileId, admin.userId)
    assert profile.status == "Suspended"
    assert audit_rows()[-1].action == "suspend_profile"
    ReactivateUserProfileController().reactivateUserProfile(profile.profileId, admin.userId)
    assert profile.status == "Active"
    assert audit_rows()[-1].action == "reactivate_profile"
    assert audit_rows()[-1].targetType == "user_profile"


def test_suspending_blocks_login_of_its_accounts(admin, make_account):
    customer = make_account(role="customer")
    assert customer.canLogIn()
    SuspendUserProfileController().suspendUserProfile(
        customer.profile.profileId, admin.userId
    )
    assert not customer.canLogIn()
    ReactivateUserProfileController().reactivateUserProfile(
        customer.profile.profileId, admin.userId
    )
    assert customer.canLogIn()


def test_suspend_refusals(admin):
    profile = create(admin)
    controller = SuspendUserProfileController()
    with pytest.raises(ValidationError):
        controller.suspendUserProfile(9999, admin.userId)
    with pytest.raises(ValidationError):
        controller.suspendUserProfile(admin.profileId, admin.userId)  # own profile
    controller.suspendUserProfile(profile.profileId, admin.userId)
    with pytest.raises(ValidationError):
        controller.suspendUserProfile(profile.profileId, admin.userId)  # already suspended
    assert len(audit_rows()) == 2  # create and the one suspend


def test_reactivate_refusals(admin):
    profile = create(admin)
    controller = ReactivateUserProfileController()
    with pytest.raises(ValidationError):
        controller.reactivateUserProfile(9999, admin.userId)
    with pytest.raises(ValidationError):
        controller.reactivateUserProfile(profile.profileId, admin.userId)  # not suspended


# US-31 search


def test_search_profiles_by_keyword_role_and_status(admin):
    support = create(admin, name="Support Staff", description="Helps users")
    create(admin, name="Contractor", roleType="designer")
    SuspendUserProfileController().suspendUserProfile(support.profileId, admin.userId)
    search = SearchUserProfilesController().searchUserProfiles
    assert [p.name for p in search("support", "", "")] == ["Support Staff"]
    assert [p.name for p in search("HELPS", "", "")] == ["Support Staff"]
    assert {p.name for p in search("", "designer", "")} == {"Interior Designer", "Contractor"}
    assert [p.name for p in search("", "", "Suspended")] == ["Support Staff"]
    assert search("nothing", "", "") == []
    assert len(search("", "", "")) == 6
