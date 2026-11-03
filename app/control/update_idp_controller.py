from app.control.idp_validation import findInvalidPhoto, findMissingFields
from app.entity import IDPEntity


class UpdateIDPController:
    """US-40 (with US-45): a designer changes one of their own IDPs and adds or removes photos.

    Returns None when the IDP is not theirs, then the same results as AddIDPController:
    True, False (category suspended), a list of missing field names or a photo message.
    At least one photo must remain.
    """

    def __init__(self):
        self.entity = IDPEntity

    def updateIDP(self, designerId, idpId, idp, photos):
        current = self.entity.getMyIDP(designerId, idpId)
        if current is None:
            return None
        removed = set(idp.get("removePhotos") or []) & set(current.photoUrls)
        remaining = len(current.photoUrls) - len(removed) + len(photos)
        missing = findMissingFields(idp, remaining)
        if missing:
            return missing
        invalid = findInvalidPhoto(photos)
        if invalid is not None:
            return invalid
        return self.entity.updateIDP(designerId, idpId, idp, photos)
