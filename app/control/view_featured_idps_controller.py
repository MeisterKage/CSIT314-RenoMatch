from app.entity import IDPEntity


class ViewFeaturedIDPsController:
    """US-60 page listings: the featured slots and the Active IDPs to choose from."""

    def __init__(self):
        self.entity = IDPEntity

    def getFeaturedIDPs(self):
        return self.entity.getFeaturedSlots()

    def searchActiveIDPs(self, keyword, page):
        return self.entity.searchIDPs(keyword, None, None, None, None, None, page)
