import csv
import io
from datetime import date, datetime

import pytest

from app.control.export_user_accounts_controller import ExportUserAccountsController
from app.control.view_audit_log_controller import ViewAuditLogController
from app.entity import AuditLogEntity, UserAccountEntity, db


@pytest.fixture
def admin(make_account):
    return make_account(role="admin", username="boss")


def addLog(admin, action, when):
    """Audit rows are read-only through the ORM, so the time is set with a table update."""
    row = AuditLogEntity.recordAction(admin.userId, action, "user_account", 1)
    db.session.execute(
        AuditLogEntity.__table__.update()
        .where(AuditLogEntity.__table__.c.id == row.logId)
        .values(timestamp=when)
    )
    db.session.commit()
    return row


# US-32


def test_audit_log_newest_first_and_unfiltered(admin):
    addLog(admin, "first", datetime(2026, 1, 1, 9))
    addLog(admin, "second", datetime(2026, 3, 1, 9))
    logs = ViewAuditLogController().getAuditLogs(None, None)
    assert [row.action for row in logs] == ["second", "first"]


def test_audit_log_range_includes_both_end_days(admin):
    addLog(admin, "a", datetime(2026, 1, 1, 0, 5))
    addLog(admin, "b", datetime(2026, 1, 31, 23, 55))
    addLog(admin, "c", datetime(2026, 2, 1, 0, 5))
    addLog(admin, "d", datetime(2025, 12, 31, 23, 55))
    logs = ViewAuditLogController().getAuditLogs(date(2026, 1, 1), date(2026, 1, 31))
    assert [row.action for row in logs] == ["b", "a"]


def test_audit_log_with_only_one_bound(admin):
    addLog(admin, "a", datetime(2026, 1, 1, 9))
    addLog(admin, "b", datetime(2026, 5, 1, 9))
    controller = ViewAuditLogController()
    assert [r.action for r in controller.getAuditLogs(date(2026, 3, 1), None)] == ["b"]
    assert [r.action for r in controller.getAuditLogs(None, date(2026, 3, 1))] == ["a"]


def test_audit_log_start_after_end_returns_none_without_calling_entity(admin):
    class Spy:
        called = False

        @classmethod
        def getAuditLogs(cls, startDate, endDate):
            cls.called = True
            return []

    controller = ViewAuditLogController()
    controller.entity = Spy
    assert controller.getAuditLogs(date(2026, 2, 1), date(2026, 1, 1)) is None
    assert Spy.called is False


def test_audit_log_no_records_returns_empty_list(admin):
    assert ViewAuditLogController().getAuditLogs(date(2026, 1, 1), date(2026, 1, 2)) == []


def test_audit_log_controller_passes_the_dates_to_the_entity(admin):
    seen = []

    class Spy:
        @classmethod
        def getAuditLogs(cls, startDate, endDate):
            seen.append((startDate, endDate))
            return ["x"]

    controller = ViewAuditLogController()
    controller.entity = Spy
    assert controller.getAuditLogs(date(2026, 1, 1), date(2026, 1, 2)) == ["x"]
    assert seen == [(date(2026, 1, 1), date(2026, 1, 2))]


# US-34


def parse(csvFile):
    return list(csv.reader(io.StringIO(csvFile)))


def test_export_returns_none_when_no_accounts(app, default_profiles):
    assert ExportUserAccountsController().exportUserAccountsCSV("", "", "") is None


def test_export_columns_and_rows_never_include_passwords(admin, make_account):
    make_account(role="designer", username="dana", name="Dana Tan", email="dana@example.com")
    rows = parse(ExportUserAccountsController().exportUserAccountsCSV("", "", ""))
    assert rows[0] == ["User ID", "Name", "Email", "User profile", "Status", "Date created"]
    assert len(rows) == 3
    dana = UserAccountEntity.findByUsername("dana")
    assert rows[2][:5] == [
        str(dana.userId),
        "Dana Tan",
        "dana@example.com",
        "Interior Designer",
        "Active",
    ]
    assert rows[2][5] == dana.createdAt.strftime("%Y-%m-%d")
    text = "".join(",".join(r) for r in rows).lower()
    assert "pbkdf2" not in text and "scrypt" not in text and "password" not in text


def test_export_applies_the_filters(admin, make_account):
    make_account(role="designer", username="dana", name="Dana Tan")
    make_account(role="customer", username="carl", name="Carl Ng").suspend()
    controller = ExportUserAccountsController()
    by_keyword = parse(controller.exportUserAccountsCSV("dana", "", ""))
    assert [r[1] for r in by_keyword[1:]] == ["Dana Tan"]
    by_both = parse(controller.exportUserAccountsCSV("", "Customer", "Suspended"))
    assert [r[1] for r in by_both[1:]] == ["Carl Ng"]
    assert controller.exportUserAccountsCSV("nobody", "", "") is None


def test_export_neutralises_spreadsheet_formulas(admin, make_account):
    make_account(username="evil", name='=HYPERLINK("x")')
    rows = parse(ExportUserAccountsController().exportUserAccountsCSV("evil", "", ""))
    assert rows[1][1].startswith("'=")
