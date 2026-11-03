from app.control.create_category_controller import category_errors
from app.control.errors import ValidationError
from app.entity import CategoryEntity


class UpdateCategoryController:
    """US-51: a platform manager changes a category's name and description."""

    def __init__(self):
        self.entity = CategoryEntity

    def updateCategory(self, categoryId: int, name, description) -> CategoryEntity:
        category = self.entity.findById(categoryId)
        if category is None:
            raise ValidationError({"category": "Category not found."})
        name, description = name.strip(), description.strip()
        errors = category_errors(self.entity, name, description, categoryId)
        if errors:
            raise ValidationError(errors)
        category.updateCategory(name, description)
        return category
