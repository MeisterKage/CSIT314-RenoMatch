from app.entity import IDPFlagEntity


class ResolveReportedIDPController:
    """US-58: a platform manager upholds or dismisses a report. decision is "uphold" or
    "dismiss". Returns False when the report is missing or already resolved."""

    def __init__(self):
        self.entity = IDPFlagEntity

    def resolveReport(self, flagId, managerId, decision):
        return self.entity.resolveReport(flagId, managerId, decision)
