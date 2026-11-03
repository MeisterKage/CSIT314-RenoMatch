from app.entity import AuditLogEntity


class ViewAuditLogController:
    """US-32: an administrator views the audit log, optionally for a date range."""

    def __init__(self):
        self.entity = AuditLogEntity

    def getAuditLogs(self, startDate, endDate):
        """1.1: [valid date range] ask the entity (1.1.1) and return its logs, which may be an
        empty list (2a). [4a. start date after end date] return None without asking it."""
        if startDate is not None and endDate is not None and startDate > endDate:
            return None
        return self.entity.getAuditLogs(startDate, endDate)
