from app.entity import PlatformActivityEntity
from app.entity.reports import Report


class GenerateDailyReportController:
    """US-55: a platform manager generates the report for one day, against the day before."""

    def __init__(self):
        self.entity = PlatformActivityEntity

    def generateDailyReport(self, date) -> Report:
        report = self.entity.generateReport(date, date)
        report.reportType = "daily"
        report.previous.reportType = "daily"
        return report
