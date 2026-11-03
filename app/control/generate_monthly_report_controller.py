from app.entity import PlatformActivityEntity
from app.entity.db import utcnow
from app.entity.reports import Report


class GenerateMonthlyReportController:
    """US-56: a platform manager generates the report for one month."""

    def __init__(self):
        self.entity = PlatformActivityEntity

    def generateMonthlyReport(self, month: int, year: int) -> Report | None:
        """1.1: [month not in the future] ask the entity (1.1.1) and return its report, which
        may have no activity (3a). [2a. future month selected] return None without asking it."""
        today = utcnow().date()
        if (year, month) > (today.year, today.month):
            return None
        return self.entity.generateMonthlyReport(month, year)
