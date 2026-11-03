import pytest

from app.boundary.admin import ManageUserAccountsPage, UserAccountFormPage
from app.entity import AuditLogEntity, UserAccountEntity, db

NEW_FORM = {
    "username": "newbie",
    "name": "New Bie",
    "email": "newbie@example.com",
    "phone": "91234567",
    "password": "Passw0rd!",
}


@pytest.fixture
def admin(make_account, login):
    account = make_account(role="admin", username="boss", name="Boss Person")
    login("boss")
    return account


def text(resp):
    return resp.get_data(as_text=True)


def lock(account):
    for _ in range(5):
        account.registerFailedLogin()


# Access


@pytest.mark.parametrize(
    "path",
    ["/admin/accounts", "/admin/accounts/new", "/admin/accounts/1", "/admin/accounts/1/edit"],
)
def test_pages_need_an_admin(client, make_account, login, path):
    make_account(role="customer", username="cust")
    assert client.get(path).status_code == 302
    login("cust")
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("action", ["suspend", "reactivate", "unlock"])
def test_actions_need_an_admin(client, make_account, login, action):
    target = make_account(role="customer", username="cust")
    login("cust")
    assert client.post(f"/admin/accounts/{target.userId}/{action}").status_code == 403


def test_page_classes_keep_the_controller_attribute_free_for_export(app):
    page = ManageUserAccountsPage()
    assert not hasattr(page, "controller")
    assert hasattr(page, "searchController")
    assert not hasattr(UserAccountFormPage(), "controller")


# Navigation


def test_admin_nav_and_home_link_to_accounts(client, admin):
    assert 'href="/admin/accounts"' in text(client.get("/admin/"))
    assert ">Accounts<" in text(client.get("/account"))


def test_other_roles_do_not_see_the_accounts_link(client, make_account, login):
    make_account(role="customer", username="cust")
    login("cust")
    assert 'href="/admin/accounts"' not in text(client.get("/account"))


# US-25 list and search


def test_list_shows_accounts_with_profile_and_status(client, admin, make_account):
    make_account(role="designer", username="dana", name="Dana Tan")
    page = text(client.get("/admin/accounts"))
    assert "dana" in page
    assert "Dana Tan" in page
    assert "Interior Designer" in page
    assert "Active" in page


def test_list_has_a_disabled_export_button_placeholder(client, admin):
    page = text(client.get("/admin/accounts"))
    assert "Export CSV" in page
    assert "disabled" in page


def test_search_by_keyword_profile_and_status(client, admin, make_account):
    make_account(role="designer", username="dana", name="Dana Tan")
    make_account(role="customer", username="carl", name="Carl Ng").suspend()
    page = text(client.get("/admin/accounts?keyword=dana"))
    assert "Dana Tan" in page and "Carl Ng" not in page
    page = text(client.get("/admin/accounts?profile=Customer"))
    assert "Carl Ng" in page and "Dana Tan" not in page
    page = text(client.get("/admin/accounts?status=Suspended"))
    assert "Carl Ng" in page and "Dana Tan" not in page


def test_search_without_matches_says_so(client, admin):
    page = text(client.get("/admin/accounts?keyword=nobody-at-all"))
    assert "No accounts match your search." in page


def test_list_is_paged_and_keeps_filters(client, admin, make_account):
    for n in range(30):
        make_account(role="customer", username=f"cust{n:02d}", name=f"Cust {n:02d}")
    first = text(client.get("/admin/accounts?profile=Customer"))
    assert "cust00" in first and "cust29" not in first
    assert "page=2" in first and "profile=Customer" in first
    second = text(client.get("/admin/accounts?profile=Customer&page=2"))
    assert "cust29" in second and "cust00" not in second


# US-33 locked badge and unlock


def test_locked_account_shows_a_badge_and_unlock_button(client, admin, make_account):
    target = make_account(username="lockedy")
    page = text(client.get("/admin/accounts"))
    assert "Locked" not in page
    lock(target)
    page = text(client.get("/admin/accounts"))
    assert "Locked" in page
    assert f"/admin/accounts/{target.userId}/unlock" in page


def test_unlock_clears_the_lock_and_logs_it(client, admin, make_account):
    target = make_account(username="lockedy")
    lock(target)
    resp = client.post(f"/admin/accounts/{target.userId}/unlock")
    assert resp.status_code == 302
    assert not target.isLocked()
    assert target.failedLogins == 0
    row = AuditLogEntity.query.one()
    assert (row.action, row.targetId, row.adminId) == (
        "unlock_account",
        target.userId,
        admin.userId,
    )
    assert "unlocked" in text(client.get("/admin/accounts"))


def test_the_unlocked_user_can_log_in_again(client, admin, make_account):
    target = make_account(username="lockedy")
    lock(target)
    client.post(f"/admin/accounts/{target.userId}/unlock")
    client.post("/logout")
    resp = client.post("/login", data={"username": "lockedy", "password": "Passw0rd!"})
    assert resp.status_code == 302


# US-20 create


def test_create_form_offers_every_profile(client, admin):
    page = text(client.get("/admin/accounts/new"))
    for name in ("User Admin", "Interior Designer", "Customer", "Platform Manager"):
        assert name in page


def test_create_account_redirects_to_its_page_and_logs_it(client, admin, default_profiles):
    resp = client.post(
        "/admin/accounts/new",
        data=dict(NEW_FORM, profileId=default_profiles["platform"].profileId),
    )
    created = UserAccountEntity.findByUsername("newbie")
    assert resp.status_code == 302
    assert resp.headers["Location"] == f"/admin/accounts/{created.userId}"
    assert created.role == "platform"
    row = AuditLogEntity.query.one()
    assert (row.action, row.targetId) == ("create_account", created.userId)


def test_create_account_shows_field_errors_and_keeps_input(client, admin, default_profiles):
    data = dict(NEW_FORM, profileId=default_profiles["customer"].profileId, email="bad")
    resp = client.post("/admin/accounts/new", data=data)
    page = text(resp)
    assert resp.status_code == 200
    assert "Enter a valid email address." in page
    assert 'value="newbie"' in page
    assert "Passw0rd!" not in page
    assert UserAccountEntity.findByUsername("newbie") is None


def test_create_account_needs_a_profile(client, admin):
    resp = client.post("/admin/accounts/new", data=NEW_FORM)
    assert "Choose a profile." in text(resp)


# US-21 view


def test_view_page_shows_details_and_never_the_password_hash(client, admin, make_account):
    target = make_account(role="designer", username="dana", name="Dana Tan", phone="91234567")
    page = text(client.get(f"/admin/accounts/{target.userId}"))
    for expected in ("dana", "Dana Tan", target.email, "91234567", "Interior Designer", "Active"):
        assert expected in page
    assert target.passwordHash not in page


def test_view_missing_account_is_404(client, admin):
    assert client.get("/admin/accounts/99999").status_code == 404


# US-22 update


def test_edit_form_is_filled_in(client, admin, make_account):
    target = make_account(name="Dana Tan")
    page = text(client.get(f"/admin/accounts/{target.userId}/edit"))
    assert 'value="Dana Tan"' in page


def test_edit_account_saves_and_logs_it(client, admin, make_account, default_profiles):
    target = make_account(role="customer")
    resp = client.post(
        f"/admin/accounts/{target.userId}/edit",
        data={
            "name": "Renamed",
            "email": "renamed@example.com",
            "phone": "",
            "profileId": default_profiles["designer"].profileId,
        },
    )
    assert resp.status_code == 302
    assert (target.name, target.role) == ("Renamed", "designer")
    assert AuditLogEntity.query.one().action == "update_account"


def test_edit_account_shows_errors(client, admin, make_account):
    target = make_account()
    resp = client.post(
        f"/admin/accounts/{target.userId}/edit",
        data={"name": "", "email": target.email, "phone": "", "profileId": target.profileId},
    )
    assert "Enter the full name." in text(resp)
    assert AuditLogEntity.query.count() == 0


# US-23 and US-24 suspend and reactivate


def test_suspend_then_reactivate(client, admin, make_account):
    target = make_account(username="victim")
    assert client.post(f"/admin/accounts/{target.userId}/suspend").status_code == 302
    assert target.status == "Suspended"
    page = text(client.get("/admin/accounts"))
    assert f"/admin/accounts/{target.userId}/reactivate" in page
    client.post(f"/admin/accounts/{target.userId}/reactivate")
    assert target.status == "Active"
    assert [r.action for r in AuditLogEntity.query.order_by(AuditLogEntity.logId)] == [
        "suspend_account",
        "reactivate_account",
    ]


def test_suspended_user_cannot_log_in(client, admin, make_account):
    target = make_account(username="victim")
    client.post(f"/admin/accounts/{target.userId}/suspend")
    client.post("/logout")
    resp = client.post("/login", data={"username": "victim", "password": "Passw0rd!"})
    assert "suspended" in text(resp)


def test_admin_cannot_suspend_themselves(client, admin):
    resp = client.post(f"/admin/accounts/{admin.userId}/suspend", follow_redirects=True)
    assert "You cannot suspend your own account." in text(resp)
    assert db.session.get(UserAccountEntity, admin.userId).status == "Active"
    assert AuditLogEntity.query.count() == 0


def test_own_row_has_no_suspend_button(client, admin):
    page = text(client.get("/admin/accounts"))
    assert f"/admin/accounts/{admin.userId}/suspend" not in page
