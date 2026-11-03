from app.control.errors import ValidationError
from app.entity import CategoryEntity


class SuspendCategoryController:
    """US-52: a platform manager suspends a category. It disappears from the browse filters
    and the add-IDP list, and its IDPs stay as they are."""

    def __init__(self):
        self.entity = CategoryEntity

    def suspendCategory(self, categoryId: int) -> bool:
        category = self.entity.findById(categoryId)
        if category is None:
            raise ValidationError({"category": "Category not found."})
        if category.status == "Suspended":
            raise ValidationError({"category": "That category is already suspended."})
        category.suspend()
        return True
