from app.entity import IDPEntity

FEATURED_LIMIT = 6


class FeatureIDPController:
    """US-60: a platform manager features and unfeatures IDPs on the home page.

    featureIDP follows the sequence diagram. It counts the featured IDPs (1.1.1). With fewer
    than 6 [count < 6] it returns the entity's result for setFeatured (1.1.2), which is False
    for an IDP that is suspended or removed (5a). Otherwise [4a. 6 IDPs already featured] it
    returns False. `limitReached` tells the page which of the two False cases happened.
    """

    def __init__(self):
        self.entity = IDPEntity
        self.limitReached = False

    def featureIDP(self, idpId):
        count = self.entity.countFeaturedIDPs()  # 1.1.1
        self.limitReached = count >= FEATURED_LIMIT
        if count < FEATURED_LIMIT:  # [count < 6]
            return self.entity.setFeatured(idpId, True)  # 1.1.2
        return False  # [4a. 6 IDPs already featured]

    def unfeatureIDP(self, idpId):
        return self.entity.setFeatured(idpId, False)  # 2.1.1
