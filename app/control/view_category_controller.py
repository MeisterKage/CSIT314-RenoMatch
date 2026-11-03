from app.entity import CategoryEntity


class ViewCategoryController:
    """US-50: a platform manager views a category, including its idpCount."""

    def __init__(self):
        self.entity = CategoryEntity

    def getCategory(self, categoryId: int) -> CategoryEntity | None:
        return self.entity.findById(categoryId)
