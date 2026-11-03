from app.entity import IDPEntity


class ViewIDPViewCountController:
    """US-43: the view count of one IDP."""

    def __init__(self):
        self.entity = IDPEntity

    def getViewCount(self, idpId):
        """1.1: ask the entity (1.1.1) and return the viewCount."""
        return self.entity.getViewCount(idpId)
