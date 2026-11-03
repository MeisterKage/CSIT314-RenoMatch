from fpdf import FPDF

from app.control.generate_custom_report_controller import GenerateCustomReportController
from app.control.generate_daily_report_controller import GenerateDailyReportController
from app.control.generate_monthly_report_controller import GenerateMonthlyReportController
from app.control.report_params import parseDate, parseMonthYear
from app.entity.reports import REPORT_FIGURES, Report

TITLES = {
    "daily": "Daily Activity Report",
    "monthly": "Monthly Activity Report",
    "custom": "Custom Range Activity Report",
}


def formatDay(day) -> str:
    return f"{day.day} {day.strftime('%b %Y')}"


def formatPeriod(startDate, endDate) -> str:
    if startDate == endDate:
        return formatDay(startDate)
    return f"{formatDay(startDate)} to {formatDay(endDate)}"


def formatChange(change: int) -> str:
    return f"+{change}" if change > 0 else str(change)


class ExportReportPDFController:
    """US-57: a platform manager downloads the report shown on the reports page as a PDF."""

    def __init__(self):
        self.dailyController = GenerateDailyReportController()
        self.monthlyController = GenerateMonthlyReportController()
        self.customController = GenerateCustomReportController()

    def exportReportPDF(self, reportType, params) -> bytes | None:
        """The one-page PDF for the report that `reportType` and `params` describe, using the
        same rules as the page. None when the parameters are unusable, such as a future month."""
        report = None
        if reportType == "daily":
            day = parseDate(params.get("date"))
            if day is not None:
                report = self.dailyController.generateDailyReport(day)
        elif reportType == "monthly":
            monthYear = parseMonthYear(params.get("month"), params.get("year"))
            if monthYear is not None:
                report = self.monthlyController.generateMonthlyReport(*monthYear)
        elif reportType == "custom":
            start, end = parseDate(params.get("startDate")), parseDate(params.get("endDate"))
            if start is not None and end is not None:
                report = self.customController.generateCustomReport(start, end)
        if report is None:
            return None
        return self.buildPDF(report)

    @staticmethod
    def buildPDF(report: Report) -> bytes:
        """One A4 page in a core font, so every character stays inside Latin-1."""
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, "RenoMatch", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 15)
        title = TITLES.get(report.reportType, "Activity Report")
        pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0, 7, f"Period: {formatPeriod(report.startDate, report.endDate)}",
            new_x="LMARGIN", new_y="NEXT",
        )
        previous = report.previous
        if previous is not None:
            pdf.cell(
                0, 7, f"Compared with: {formatPeriod(previous.startDate, previous.endDate)}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(6)

        widths = (80, 35, 35, 30)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(230, 236, 230)
        for width, heading in zip(widths, ("Figure", "This period", "Previous", "Change")):
            align = "L" if heading == "Figure" else "R"
            pdf.cell(width, 9, heading, border=1, align=align, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 11)
        for figure, label in REPORT_FIGURES:
            cells = (
                label,
                str(getattr(report, figure)),
                str(getattr(previous, figure)) if previous is not None else "-",
                formatChange(report.change(figure)),
            )
            for index, (width, value) in enumerate(zip(widths, cells)):
                pdf.cell(width, 9, value, border=1, align="L" if index == 0 else "R")
            pdf.ln()
        if not report.hasActivity:
            pdf.ln(6)
            pdf.cell(0, 7, "There was no activity in this period.", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
