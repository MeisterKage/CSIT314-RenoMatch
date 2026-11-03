from app.control.errors import ValidationError
from app.entity import CategoryEntity


class ReactivateCategoryController:
    """US-53: a platform manager makes a suspended category available again."""

    def __init__(self):
        self.entity = CategoryEntity

    def reactivateCategory(self, categoryId: int) -> bool:
        category = self.entity.findById(categoryId)
        if category is None:
            raise ValidationError({"category": "Category not found."})
        if category.status == "Active":
            raise ValidationError({"category": "That category is already active."})
        category.reactivate()
        return True
