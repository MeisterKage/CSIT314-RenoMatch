from app.entity import IDPEntity


class SearchIDPsController:
    """US-09: search Active IDPs by keyword, category, style, property type and budget."""

    def __init__(self):
        self.entity = IDPEntity

    def searchIDPs(
        self, keyword, categoryId, style, propertyType, minBudget, maxBudget, page: int = 1
    ):
        return self.entity.searchIDPs(
            keyword, categoryId, style, propertyType, minBudget, maxBudget, page
        )
