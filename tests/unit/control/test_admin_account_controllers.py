import pytest

from app.control.create_user_account_controller import CreateUserAccountController
from app.control.errors import ValidationError
from app.control.reactivate_user_account_controller import ReactivateUserAccountController
from app.control.search_user_accounts_controller import SearchUserAccountsController
from app.control.suspend_user_account_controller import SuspendUserAccountController
from app.control.unlock_user_account_controller import UnlockUserAccountController
from app.control.update_user_account_controller import UpdateUserAccountController
from app.control.view_user_account_controller import ViewUserAccountController
from app.entity import AuditLogEntity, UserAccountEntity, db

NEW = {
    "username": "newbie",
    "email": "newbie@example.com",
    "password": "Passw0rd!",
    "name": "New Bie",
    "phone": "91234567",
}


@pytest.fixture
def admin(make_account):
    return make_account(role="admin", username="boss")


def audit_rows():
    return AuditLogEntity.query.order_by(AuditLogEntity.logId).all()


# US-20 create


def test_create_account_with_any_profile(admin, default_profiles):
    for role in ("admin", "designer", "customer", "platform"):
        data = dict(NEW, username=f"u_{role}", email=f"{role}@example.com")
        account = CreateUserAccountController().createUserAccount(
            profileId=default_profiles[role].profileId, adminId=admin.userId, **data
        )
        assert account.role == role
        assert account.checkPassword("Passw0rd!")


def test_create_writes_an_audit_row(admin, default_profiles):
    account = CreateUserAccountController().createUserAccount(
        profileId=default_profiles["customer"].profileId, adminId=admin.userId, **NEW
    )
    (row,) = audit_rows()
    assert (row.adminId, row.action, row.targetType, row.targetId) == (
        admin.userId,
        "create_account",
        "user_account",
        account.userId,
    )
    assert "newbie" in row.details
    assert "Passw0rd!" not in row.details


@pytest.mark.parametrize(
    "change, field",
    [
        ({"username": "x"}, "username"),
        ({"email": "nope"}, "email"),
        ({"password": "short"}, "password"),
        ({"name": "  "}, "name"),
        ({"phone": "12"}, "phone"),
        ({"profileId": 99999}, "profileId"),
    ],
)
def test_create_rejects_invalid_fields_without_audit(admin, default_profiles, change, field):
    data = dict(NEW, profileId=default_profiles["customer"].profileId)
    data.update(change)
    with pytest.raises(ValidationError) as error:
        CreateUserAccountController().createUserAccount(adminId=admin.userId, **data)
    assert field in error.value.errors
    assert audit_rows() == []
    assert UserAccountEntity.findByUsername("newbie") is None


def test_create_rejects_taken_username_and_email(admin, default_profiles, make_account):
    make_account(username="newbie", email="newbie@example.com")
    with pytest.raises(ValidationError) as error:
        CreateUserAccountController().createUserAccount(
            profileId=default_profiles["customer"].profileId, adminId=admin.userId, **NEW
        )
    assert set(error.value.errors) == {"username", "email"}


def test_create_rejects_a_suspended_profile(admin, default_profiles):
    default_profiles["customer"].status = "Suspended"
    db.session.commit()
    with pytest.raises(ValidationError) as error:
        CreateUserAccountController().createUserAccount(
            profileId=default_profiles["customer"].profileId, adminId=admin.userId, **NEW
        )
    assert "profileId" in error.value.errors


# US-21 view


def test_get_user_account(make_account):
    account = make_account()
    controller = ViewUserAccountController()
    assert controller.getUserAccount(account.userId) is account
    assert controller.getUserAccount(99999) is None


# US-22 update


def test_update_changes_the_account_and_writes_an_audit_row(admin, make_account, default_profiles):
    account = make_account(role="customer")
    result = UpdateUserAccountController().updateUserAccount(
        account.userId,
        name="Renamed",
        email="renamed@example.com",
        phone="",
        profileId=default_profiles["designer"].profileId,
        adminId=admin.userId,
    )
    assert result is True
    assert (account.name, account.email, account.role) == (
        "Renamed",
        "renamed@example.com",
        "designer",
    )
    (row,) = audit_rows()
    assert (row.action, row.targetId, row.adminId) == (
        "update_account",
        account.userId,
        admin.userId,
    )


def test_update_rejects_bad_details_and_taken_email(admin, make_account):
    account = make_account()
    other = make_account()
    with pytest.raises(ValidationError) as error:
        UpdateUserAccountController().updateUserAccount(
            account.userId,
            name="",
            email=other.email,
            phone="1",
            profileId=account.profileId,
            adminId=admin.userId,
        )
    assert set(error.value.errors) == {"name", "email", "phone"}
    assert audit_rows() == []


def test_update_lets_the_account_keep_its_own_email(admin, make_account):
    account = make_account()
    assert UpdateUserAccountController().updateUserAccount(
        account.userId, "Same", account.email, "", account.profileId, admin.userId
    )


def test_admin_cannot_move_their_own_account_to_another_profile(admin, default_profiles):
    with pytest.raises(ValidationError) as error:
        UpdateUserAccountController().updateUserAccount(
            admin.userId,
            admin.name,
            admin.email,
            "",
            default_profiles["customer"].profileId,
            admin.userId,
        )
    assert "profileId" in error.value.errors
    assert admin.role == "admin"


# US-23 and US-24 suspend and reactivate


def test_suspend_and_reactivate_write_audit_rows(admin, make_account):
    account = make_account()
    assert SuspendUserAccountController().suspendUserAccount(account.userId, admin.userId)
    assert account.status == "Suspended"
    assert ReactivateUserAccountController().reactivateUserAccount(account.userId, admin.userId)
    assert account.status == "Active"
    assert [(r.action, r.targetType, r.targetId) for r in audit_rows()] == [
        ("suspend_account", "user_account", account.userId),
        ("reactivate_account", "user_account", account.userId),
    ]


def test_admin_cannot_suspend_their_own_account(admin):
    with pytest.raises(ValidationError, match="your own account"):
        SuspendUserAccountController().suspendUserAccount(admin.userId, admin.userId)
    assert admin.status == "Active"
    assert audit_rows() == []


def test_suspending_a_suspended_account_and_reactivating_an_active_one_are_refused(
    admin, make_account
):
    account = make_account()
    with pytest.raises(ValidationError, match="already active"):
        ReactivateUserAccountController().reactivateUserAccount(account.userId, admin.userId)
    SuspendUserAccountController().suspendUserAccount(account.userId, admin.userId)
    with pytest.raises(ValidationError, match="already suspended"):
        SuspendUserAccountController().suspendUserAccount(account.userId, admin.userId)
    assert len(audit_rows()) == 1


def test_actions_on_a_missing_account_are_refused(admin):
    for call in (
        lambda: SuspendUserAccountController().suspendUserAccount(99999, admin.userId),
        lambda: ReactivateUserAccountController().reactivateUserAccount(99999, admin.userId),
        lambda: UnlockUserAccountController().unlockUserAccount(99999, admin.userId),
    ):
        with pytest.raises(ValidationError, match="not found"):
            call()


# US-25 search


def test_search_user_accounts_delegates_to_the_entity(make_account):
    make_account(username="ann", name="Ann")
    make_account(username="bob", name="Bob")
    found = SearchUserAccountsController().searchUserAccounts("ann", "", "")
    assert [a.username for a in found] == ["ann"]


# US-33 unlock


def test_unlock_clears_the_lock_and_writes_an_audit_row(admin, make_account):
    account = make_account()
    for _ in range(5):
        account.registerFailedLogin()
    assert UnlockUserAccountController().unlockUserAccount(account.userId, admin.userId)
    assert not account.isLocked()
    assert account.failedLogins == 0
    (row,) = audit_rows()
    assert (row.action, row.targetId, row.adminId) == (
        "unlock_account",
        account.userId,
        admin.userId,
    )


def test_unlock_refuses_an_account_that_is_not_locked(admin, make_account):
    with pytest.raises(ValidationError, match="not locked"):
        UnlockUserAccountController().unlockUserAccount(make_account().userId, admin.userId)
    assert audit_rows() == []
