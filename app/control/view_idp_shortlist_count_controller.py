from app.entity import IDPEntity


class ViewIDPShortlistCountController:
    """US-44: the shortlist count of one IDP."""

    def __init__(self):
        self.entity = IDPEntity

    def getShortlistCount(self, idpId):
        return self.entity.getShortlistCount(idpId)
