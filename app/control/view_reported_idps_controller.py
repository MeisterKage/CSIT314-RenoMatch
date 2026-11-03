from app.entity import IDPFlagEntity


class ViewReportedIDPsController:
    """US-58: a platform manager views the Open reports on IDPs."""

    def __init__(self):
        self.entity = IDPFlagEntity

    def getOpenReports(self):
        return self.entity.getOpenReports()
