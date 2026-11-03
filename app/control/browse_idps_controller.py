from app.entity import IDPEntity


class BrowseIDPsController:
    """US-01: browse Active IDPs without filters."""

    def __init__(self):
        self.entity = IDPEntity

    def getActiveIDPs(self, page: int = 1):
        return self.entity.getActiveIDPs(page)
