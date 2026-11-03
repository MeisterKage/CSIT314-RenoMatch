from datetime import datetime

import pytest

from app.boundary.admin import ManageUserAccountsPage
from app.boundary.audit_log import AuditLogPage
from app.control.export_user_accounts_controller import ExportUserAccountsController
from app.control.view_audit_log_controller import ViewAuditLogController
from app.entity import AuditLogEntity, db


@pytest.fixture
def admin(make_account, login):
    account = make_account(role="admin", username="boss", name="Boss Person")
    login("boss")
    return account


def text(resp):
    return resp.get_data(as_text=True)


def addLog(admin, action, when, targetId=7):
    row = AuditLogEntity.recordAction(admin.userId, action, "user_account", targetId)
    db.session.execute(
        AuditLogEntity.__table__.update()
        .where(AuditLogEntity.__table__.c.id == row.logId)
        .values(timestamp=when)
    )
    db.session.commit()


# US-32


def test_audit_log_needs_an_admin(client, make_account, login):
    assert client.get("/admin/audit-log").status_code == 302
    make_account(role="customer", username="cust")
    login("cust")
    assert client.get("/admin/audit-log").status_code == 403


def test_audit_page_wires_controller(app):
    assert isinstance(AuditLogPage().controller, ViewAuditLogController)


def test_audit_log_lists_entries_newest_first_and_is_read_only(client, admin):
    addLog(admin, "suspend_account", datetime(2026, 1, 1, 9, 30), targetId=11)
    addLog(admin, "create_account", datetime(2026, 2, 1, 14, 5), targetId=12)
    page = text(client.get("/admin/audit-log"))
    assert page.index("create_account") < page.index("suspend_account")
    assert "Boss Person" in page
    assert "01 Jan 2026" in page and "09:30" in page
    assert "user_account" in page and "#11" in page
    assert client.post("/admin/audit-log").status_code == 405


def test_audit_log_filters_by_date_range(client, admin):
    addLog(admin, "old_action", datetime(2026, 1, 1, 9))
    addLog(admin, "new_action", datetime(2026, 3, 1, 9))
    page = text(client.get("/admin/audit-log?startDate=2026-02-01&endDate=2026-03-31"))
    assert "new_action" in page and "old_action" not in page


def test_audit_log_empty_period_shows_message(client, admin):
    addLog(admin, "old_action", datetime(2026, 1, 1, 9))
    page = text(client.get("/admin/audit-log?startDate=2026-05-01&endDate=2026-05-02"))
    assert "No audit records found for this period" in page


def test_audit_log_start_after_end_shows_error(client, admin):
    addLog(admin, "old_action", datetime(2026, 1, 1, 9))
    page = text(client.get("/admin/audit-log?startDate=2026-05-02&endDate=2026-05-01"))
    assert "The start date must not be after the end date" in page
    assert "old_action" not in page


def test_audit_log_ignores_unreadable_dates(client, admin):
    addLog(admin, "old_action", datetime(2026, 1, 1, 9))
    assert "old_action" in text(client.get("/admin/audit-log?startDate=banana"))


def test_admin_nav_and_home_link_to_audit_log(client, admin):
    for path in ("/admin/", "/account"):
        assert 'href="/admin/audit-log"' in text(client.get(path))


# US-34


def test_manage_page_has_export_controller(app):
    assert isinstance(ManageUserAccountsPage().controller, ExportUserAccountsController)


def test_export_needs_an_admin(client, make_account, login):
    assert client.get("/admin/accounts/export").status_code == 302
    make_account(role="customer", username="cust")
    login("cust")
    assert client.get("/admin/accounts/export").status_code == 403


def test_export_downloads_csv_with_filters(client, admin, make_account):
    make_account(role="designer", username="dana", name="Dana Tan")
    make_account(role="customer", username="carl", name="Carl Ng")
    resp = client.get("/admin/accounts/export?profile=Interior+Designer")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    stamp = datetime.now().strftime("%Y-%m-%d")
    assert resp.headers["Content-Disposition"] == f"attachment; filename=user_accounts_{stamp}.csv"
    body = text(resp)
    assert body.splitlines()[0] == "User ID,Name,Email,User profile,Status,Date created"
    assert "Dana Tan" in body and "Carl Ng" not in body
    assert "pbkdf2" not in body and "scrypt" not in body


def test_export_with_no_matches_shows_message(client, admin):
    resp = client.get("/admin/accounts/export?keyword=nobody", follow_redirects=True)
    assert resp.mimetype == "text/html"
    assert "No accounts to export" in text(resp)


def test_accounts_page_export_link_uses_current_filters(client, admin):
    page = text(client.get("/admin/accounts?keyword=boss&status=Active"))
    assert "disabled" not in page
    assert 'href="/admin/accounts/export?keyword=boss&amp;status=Active"' in page
