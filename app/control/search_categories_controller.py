from app.entity import CategoryEntity


class SearchCategoriesController:
    """US-54: a platform manager searches categories by name and status."""

    def __init__(self):
        self.entity = CategoryEntity

    def searchCategories(self, keyword, status) -> list[CategoryEntity]:
        """1.1: ask the entity (1.1.1) and return its categories, which may be an empty list
        (3a). The page chooses what to display from that list."""
        return self.entity.searchCategories(keyword, status)
