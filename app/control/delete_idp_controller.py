from app.entity import IDPEntity


class DeleteIDPController:
    """US-41: a designer removes one of their own IDPs. False when it is not theirs."""

    def __init__(self):
        self.entity = IDPEntity

    def deleteIDP(self, designerId, idpId):
        return self.entity.deleteIDP(designerId, idpId)
