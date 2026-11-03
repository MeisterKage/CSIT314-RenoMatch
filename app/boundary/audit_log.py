from datetime import date

from flask import Blueprint, render_template, request
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.view_audit_log_controller import ViewAuditLogController

bp = Blueprint("audit_log", __name__, url_prefix="/admin")

NO_RECORDS = "No audit records found for this period."
BAD_RANGE = "The start date must not be after the end date."


def parseDate(value: str):
    """A yyyy-mm-dd date from the form, or None when it is blank or unreadable."""
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


class AuditLogPage(MethodView):
    """Boundary for US-32. `get` is sequence step 1 (open "Audit Log", set date range). The
    display methods take no argument, as in the class diagram, so the page holds what they
    show in `logs`, `message` and `filters`. The log is read-only: there is no POST."""

    decorators = [role_required("admin")]

    def __init__(self):
        self.controller = ViewAuditLogController()
        self.logs = []
        self.message = None
        self.filters = {"startDate": "", "endDate": ""}

    def get(self):
        self.filters = {
            "startDate": request.args.get("startDate", "").strip(),
            "endDate": request.args.get("endDate", "").strip(),
        }
        startDate = parseDate(self.filters["startDate"])
        endDate = parseDate(self.filters["endDate"])
        logs = self.controller.getAuditLogs(startDate, endDate)  # 1.1
        if logs is None:  # [4a. start date after end date]
            self.message = BAD_RANGE
            return self.displayMessage()  # 1.4
        if logs:  # [logs not empty]
            self.logs = logs
            return self.displayAuditLog()  # 1.2
        self.message = NO_RECORDS  # [2a. no records found]
        return self.displayMessage()  # 1.3

    def displayAuditLog(self):
        return render_template(
            "admin/audit_log.html", logs=self.logs, filters=self.filters, message=None
        )

    def displayMessage(self):
        return render_template(
            "admin/audit_log.html",
            logs=[],
            filters=self.filters,
            message=self.message,
            isError=self.message == BAD_RANGE,
        )


bp.add_url_rule("/audit-log", view_func=AuditLogPage.as_view("audit_log"))
