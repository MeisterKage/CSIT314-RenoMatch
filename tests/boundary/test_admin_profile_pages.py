import pytest

from app.boundary.admin import ManageUserProfilesPage, UserProfileFormPage
from app.entity import AuditLogEntity, UserProfileEntity


@pytest.fixture
def admin(make_account, login):
    account = make_account(role="admin", username="boss", name="Boss Person")
    login("boss")
    return account


def text(resp):
    return resp.get_data(as_text=True)


def audit_rows():
    return AuditLogEntity.query.order_by(AuditLogEntity.logId).all()


def make_profile(name="Support Staff", roleType="customer"):
    return UserProfileEntity.createUserProfile(name, roleType, "Helps users")


# Access and navigation


@pytest.mark.parametrize(
    "path",
    ["/admin/profiles", "/admin/profiles/new", "/admin/profiles/1", "/admin/profiles/1/edit"],
)
def test_pages_need_an_admin(client, make_account, login, path):
    make_account(role="customer", username="cust")
    assert client.get(path).status_code == 302
    login("cust")
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("action", ["suspend", "reactivate"])
def test_actions_need_an_admin(client, make_account, login, action):
    make_account(role="customer", username="cust")
    login("cust")
    assert client.post(f"/admin/profiles/1/{action}").status_code == 403


def test_page_attributes(app):
    assert hasattr(ManageUserProfilesPage(), "searchController")
    assert hasattr(UserProfileFormPage(), "createController")


def test_admin_nav_and_home_link_to_profiles(client, admin):
    assert 'href="/admin/profiles"' in text(client.get("/"))
    assert 'href="/admin/profiles"' in text(client.get("/account"))


# US-31 list and search


def test_list_and_search(client, admin):
    make_profile("Support Staff")
    make_profile("Contractor", "designer").suspend()
    page = text(client.get("/admin/profiles"))
    assert "Support Staff" in page and "Contractor" in page and "User Admin" in page
    page = text(client.get("/admin/profiles?keyword=support"))
    assert "Support Staff" in page and "Contractor" not in page
    page = text(client.get("/admin/profiles?role=designer&status=Suspended"))
    assert "Contractor" in page and "Support Staff" not in page
    assert "No profiles match your search" in text(client.get("/admin/profiles?keyword=zzz"))


# US-26 create


def test_create_profile(client, admin):
    page = client.get("/admin/profiles/new")
    assert page.status_code == 200
    resp = client.post(
        "/admin/profiles/new",
        data={"name": "Support Staff", "description": "Helps", "roleType": "customer"},
    )
    profile = UserProfileEntity.findByName("Support Staff")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/admin/profiles/{profile.profileId}")
    assert audit_rows()[-1].targetType == "user_profile"


def test_create_profile_shows_errors_and_keeps_input(client, admin):
    resp = client.post(
        "/admin/profiles/new", data={"name": "Customer", "description": "kept", "roleType": ""}
    )
    page = text(resp)
    assert resp.status_code == 200
    assert "already exists" in page
    assert "Choose a role" in page
    assert "kept" in page
    assert audit_rows() == []


# US-27 view


def test_view_shows_role_and_account_count(client, admin, make_account):
    make_account(role="customer")
    customer = UserProfileEntity.findByName("Customer")
    page = text(client.get(f"/admin/profiles/{customer.profileId}"))
    assert "customer" in page.lower()
    assert "Accounts" in page
    assert "<dd>1</dd>" in page
    assert client.get("/admin/profiles/9999").status_code == 404


# US-28 update


def test_update_profile(client, admin):
    profile = make_profile()
    page = client.get(f"/admin/profiles/{profile.profileId}/edit")
    assert "Support Staff" in text(page)
    resp = client.post(
        f"/admin/profiles/{profile.profileId}/edit",
        data={"name": "Support Team", "description": "More"},
    )
    assert resp.status_code == 302
    assert profile.name == "Support Team"
    assert audit_rows()[-1].action == "update_profile"


def test_update_profile_error_and_missing(client, admin):
    profile = make_profile()
    resp = client.post(
        f"/admin/profiles/{profile.profileId}/edit", data={"name": "", "description": ""}
    )
    assert "Enter a profile name" in text(resp)
    assert client.get("/admin/profiles/9999/edit").status_code == 404


# US-29 and US-30 suspend and reactivate


def test_suspend_then_reactivate_from_page(client, admin):
    profile = make_profile()
    resp = client.post(
        f"/admin/profiles/{profile.profileId}/suspend",
        data={"next": "/admin/profiles?keyword=sup"},
        follow_redirects=True,
    )
    assert profile.status == "Suspended"
    assert "Profile suspended." in text(resp)
    resp = client.post(
        f"/admin/profiles/{profile.profileId}/reactivate", follow_redirects=True
    )
    assert profile.status == "Active"
    assert "Profile reactivated." in text(resp)


def test_suspended_profile_accounts_cannot_log_in(client, admin, make_account):
    make_account(role="customer", username="cust")
    client.post(
        f"/admin/profiles/{UserProfileEntity.findByName('Customer').profileId}/suspend"
    )
    other = client.application.test_client()
    resp = other.post("/login", data={"username": "cust", "password": "Passw0rd!"})
    assert resp.status_code != 302


def test_cannot_suspend_own_profile(client, admin):
    resp = client.post(
        f"/admin/profiles/{admin.profileId}/suspend", follow_redirects=True
    )
    assert "cannot suspend your own profile" in text(resp)
    assert admin.profile.status == "Active"


def test_next_must_stay_under_profiles(client, admin):
    profile = make_profile()
    resp = client.post(
        f"/admin/profiles/{profile.profileId}/suspend", data={"next": "//evil.example"}
    )
    assert resp.headers["Location"].endswith("/admin/profiles")
