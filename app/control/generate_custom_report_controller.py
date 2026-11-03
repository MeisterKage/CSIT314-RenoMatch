from app.entity import PlatformActivityEntity
from app.entity.reports import Report


class GenerateCustomReportController:
    """US-59: a platform manager generates the report for a date range, against the previous
    range of the same length."""

    def __init__(self):
        self.entity = PlatformActivityEntity

    def generateCustomReport(self, startDate, endDate) -> Report | None:
        """None when the start date is after the end date."""
        if startDate > endDate:
            return None
        return self.entity.generateReport(startDate, endDate)
