from app.entity import IDPEntity


class ViewInterestDashboardController:
    """US-46: a designer's views and shortlists per style and category, and top IDPs."""

    def __init__(self):
        self.entity = IDPEntity

    def getInterestDashboard(self, designerId):
        return self.entity.getInterestDashboard(designerId)
