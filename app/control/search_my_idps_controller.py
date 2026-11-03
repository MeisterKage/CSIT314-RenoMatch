from app.entity import IDPEntity


class SearchMyIDPsController:
    """US-42: a designer searches their own IDPs. A blank keyword lists them all."""

    def __init__(self):
        self.entity = IDPEntity

    def searchMyIDPs(self, designerId, keyword):
        return self.entity.searchMyIDPs(designerId, keyword)
