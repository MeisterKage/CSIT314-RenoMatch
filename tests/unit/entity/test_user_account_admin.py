import pytest

from app.entity import AuditLogEntity, UserAccountEntity, UserProfileEntity, db


@pytest.fixture
def people(make_account):
    return {
        "ann": make_account(role="customer", username="ann", name="Ann Lee", email="ann@x.com"),
        "bob": make_account(role="designer", username="bob", name="Bob Tan", email="bob@y.com"),
        "cat": make_account(role="customer", username="cat", name="Cat Ong", email="cat@x.com"),
    }


def names(accounts):
    return [account.username for account in accounts]


def test_search_with_no_filters_returns_every_account_by_id(people):
    assert names(UserAccountEntity.searchUserAccounts("", "", "")) == ["ann", "bob", "cat"]


@pytest.mark.parametrize(
    "keyword, expected",
    [("ANN", ["ann"]), ("tan", ["bob"]), ("@x.com", ["ann", "cat"]), ("zzz", [])],
)
def test_search_keyword_matches_username_name_or_email_ignoring_case(people, keyword, expected):
    assert names(UserAccountEntity.searchUserAccounts(keyword, "", "")) == expected


def test_search_keyword_treats_percent_literally(people):
    assert UserAccountEntity.searchUserAccounts("%", "", "") == []


def test_search_filters_by_profile_name(people):
    assert names(UserAccountEntity.searchUserAccounts("", "Interior Designer", "")) == ["bob"]
    assert names(UserAccountEntity.searchUserAccounts("", "Customer", "")) == ["ann", "cat"]


def test_search_filters_by_status(people):
    people["cat"].suspend()
    assert names(UserAccountEntity.searchUserAccounts("", "", "Suspended")) == ["cat"]
    assert names(UserAccountEntity.searchUserAccounts("", "", "Active")) == ["ann", "bob"]


def test_search_combines_filters(people):
    people["cat"].suspend()
    assert names(UserAccountEntity.searchUserAccounts("x.com", "Customer", "Active")) == ["ann"]


def test_suspend_and_reactivate_change_status(people):
    people["ann"].suspend()
    assert people["ann"].status == "Suspended"
    people["ann"].reactivate()
    assert people["ann"].status == "Active"


def test_unlock_clears_lock_and_count(people):
    for _ in range(5):
        people["ann"].registerFailedLogin()
    assert people["ann"].isLocked()
    people["ann"].unlock()
    assert people["ann"].failedLogins == 0
    assert people["ann"].lockedUntil is None


def test_update_user_account_changes_details_and_profile(people, default_profiles):
    ann = people["ann"]
    ann.updateUserAccount("Ann Lim", "Ann.Lim@X.com", "91234567", default_profiles["platform"])
    assert (ann.name, ann.email, ann.phone) == ("Ann Lim", "ann.lim@x.com", "91234567")
    assert ann.role == "platform"


def test_find_profile_by_id(default_profiles):
    profile = default_profiles["admin"]
    assert UserProfileEntity.findById(profile.profileId) is profile
    assert UserProfileEntity.findById(99999) is None


def test_audit_log_record_action_stores_every_attribute(make_account):
    admin = make_account(role="admin")
    row = AuditLogEntity.recordAction(admin.userId, "suspend_account", "user_account", 7, "why")
    assert (row.adminId, row.action, row.targetType, row.targetId, row.details) == (
        admin.userId,
        "suspend_account",
        "user_account",
        7,
        "why",
    )
    assert row.timestamp is not None
    assert db.session.get(AuditLogEntity, row.logId) is row
