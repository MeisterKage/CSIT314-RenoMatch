from app.entity import IDPEntity


class ViewMyIDPController:
    """US-39: a designer views one of their own IDPs. None when it is not theirs."""

    def __init__(self):
        self.entity = IDPEntity

    def getMyIDP(self, designerId, idpId):
        return self.entity.getMyIDP(designerId, idpId)
