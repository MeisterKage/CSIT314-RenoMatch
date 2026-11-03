from app.control.idp_validation import findInvalidPhoto, findMissingFields
from app.entity import IDPEntity


class AddIDPController:
    """US-38 (with US-45): a designer adds an interior design project with photos.

    The return of addIDP follows the sequence diagram. For valid details it is the entity's
    result: True for saved, False when the category is suspended (6c). Otherwise it is
    `missingFields`, a list of field names (6a), or `invalidPhoto`, a message (6b).
    """

    def __init__(self):
        self.entity = IDPEntity
        self.missingFields: list[str] = []
        self.invalidPhoto: str | None = None

    def addIDP(self, idp, photos):
        """1.1: validate (1.1.1), then [details and photos valid] ask the entity (1.1.2)
        and return its result. Otherwise [6a] return missingFields or [6b] invalidPhoto."""
        if self.validateIDP(idp, photos):  # 1.1.1
            return self.entity.addIDP(idp, photos)  # 1.1.2
        if self.missingFields:  # [6a. required fields missing]
            return self.missingFields
        return self.invalidPhoto  # [6b. photo not JPG/PNG or over 5 MB]

    def validateIDP(self, idp, photos):
        """Private: True when every required field is valid and every photo is a JPG or PNG
        of at most 5 MB. Otherwise False, with the reason in missingFields or invalidPhoto."""
        self.missingFields = findMissingFields(idp, len(photos))
        self.invalidPhoto = findInvalidPhoto(photos)
        return not self.missingFields and self.invalidPhoto is None
