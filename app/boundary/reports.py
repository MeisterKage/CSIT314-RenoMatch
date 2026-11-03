from flask import Blueprint, Response, abort, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.export_report_pdf_controller import ExportReportPDFController
from app.control.generate_custom_report_controller import GenerateCustomReportController
from app.control.generate_daily_report_controller import GenerateDailyReportController
from app.control.generate_monthly_report_controller import GenerateMonthlyReportController
from app.control.report_params import REPORT_TYPES, parseDate, parseMonthYear, periodLabel
from app.entity.db import utcnow
from app.entity.reports import REPORT_FIGURES

bp = Blueprint("reports", __name__, url_prefix="/platform/reports")

FUTURE_MONTH = "Please select a past or current month."
PICK_MONTH = "Select a month and year."
PICK_DATE = "Select a date."
PICK_RANGE = "Select a start date and an end date."
BAD_RANGE = "The start date must not be after the end date."

PARAMETER_NAMES = {
    "daily": ("date",),
    "monthly": ("month", "year"),
    "custom": ("startDate", "endDate"),
}


class ReportsPage(MethodView):
    """Boundary for US-55 (daily), US-56 (monthly), US-57 (PDF) and US-59 (custom range).

    `controller` is the US-56 class diagram's GenerateMonthlyReportController, so the daily
    and custom range controllers use their own attribute names. The display methods take no
    argument, as in the class diagram, so the page holds what they show in `report`, `message`
    and `params`. The report is read-only: there is no POST.
    """

    decorators = [role_required("platform")]

    def __init__(self):
        self.controller = GenerateMonthlyReportController()
        self.dailyController = GenerateDailyReportController()
        self.customController = GenerateCustomReportController()
        self.exportController = ExportReportPDFController()
        self.reportType = "monthly"
        self.params = {}
        self.report = None
        self.message = None

    def get(self):
        if request.endpoint == "reports.reports_pdf":
            return self.downloadPDF()
        self.reportType = request.args.get("type", "monthly")
        if self.reportType not in REPORT_TYPES:
            self.reportType = "monthly"
        names = PARAMETER_NAMES[self.reportType]
        self.params = {name: request.args.get(name, "").strip() for name in names}
        if not any(self.params.values()):  # the form has not been submitted yet
            self.defaultParams()
            return self.displayForm()
        if self.reportType == "daily":
            return self.generateDaily()
        if self.reportType == "custom":
            return self.generateCustom()
        return self.generateMonthly()

    def generateMonthly(self):
        """US-56 step 1: select month and year, click "Generate"."""
        monthYear = parseMonthYear(self.params["month"], self.params["year"])
        if monthYear is None:
            self.message = PICK_MONTH
            return self.displayMessage()
        report = self.controller.generateMonthlyReport(*monthYear)  # 1.1
        if report is None:  # [2a. future month selected]
            self.message = FUTURE_MONTH
            return self.displayMessage()  # 1.4
        self.report = report  # [month not in the future]
        if report.hasActivity:  # [activity recorded]
            return self.displayReport()  # 1.2
        return self.displayEmptyReport()  # [3a. no activity this month] 1.3

    def generateDaily(self):
        day = parseDate(self.params["date"])
        if day is None:
            self.message = PICK_DATE
            return self.displayMessage()
        return self.showReport(self.dailyController.generateDailyReport(day))

    def generateCustom(self):
        start, end = parseDate(self.params["startDate"]), parseDate(self.params["endDate"])
        if start is None or end is None:
            self.message = PICK_RANGE
            return self.displayMessage()
        report = self.customController.generateCustomReport(start, end)
        if report is None:
            self.message = BAD_RANGE
            return self.displayMessage()
        return self.showReport(report)

    def showReport(self, report):
        self.report = report
        if report.hasActivity:
            return self.displayReport()
        return self.displayEmptyReport()

    def downloadPDF(self):
        """US-57: the PDF for the report the page is showing, named by its period."""
        reportType = request.args.get("type", "")
        params = {name: request.args.get(name, "") for name in sum(PARAMETER_NAMES.values(), ())}
        label = periodLabel(reportType, params)
        pdf = self.exportController.exportReportPDF(reportType, params) if label else None
        if pdf is None:
            abort(400)
        return Response(
            pdf,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=activity_report_{label}.pdf"},
        )

    def defaultParams(self):
        today = utcnow().date()
        self.params = {
            "daily": {"date": today.isoformat()},
            "monthly": {"month": str(today.month), "year": str(today.year)},
            "custom": {"startDate": "", "endDate": ""},
        }[self.reportType]

    def displayForm(self):
        return self.render()

    def displayReport(self):
        return self.render()

    def displayEmptyReport(self):
        return self.render(empty=True)

    def displayMessage(self):
        return self.render(isError=True)

    def render(self, empty=False, isError=False):
        pdfArgs = {"type": self.reportType, **self.params} if self.report else None
        return render_template(
            "platform/reports.html",
            reportType=self.reportType,
            params=self.params,
            report=self.report,
            figures=REPORT_FIGURES,
            empty=empty,
            message=self.message,
            isError=isError,
            pdfUrl=url_for("reports.reports_pdf", **pdfArgs) if pdfArgs else None,
            years=range(utcnow().year, utcnow().year - 6, -1),
            months=range(1, 13),
        )


bp.add_url_rule("", view_func=ReportsPage.as_view("reports"))
bp.add_url_rule("/pdf", view_func=ReportsPage.as_view("reports_pdf"))
