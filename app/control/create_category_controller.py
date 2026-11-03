from app.control.errors import ValidationError
from app.entity import CategoryEntity

NAME_MAX = 60
DESCRIPTION_MAX = 255


def category_errors(entity, name: str, description: str, exceptCategoryId=None) -> dict:
    """The name and description rules shared by create (US-49) and update (US-51)."""
    errors = {}
    if not name:
        errors["name"] = "Enter a category name."
    elif len(name) > NAME_MAX:
        errors["name"] = f"The name can be at most {NAME_MAX} characters."
    elif entity.nameTaken(name, exceptCategoryId):
        errors["name"] = "A category with that name already exists."
    if len(description) > DESCRIPTION_MAX:
        errors["description"] = f"The description can be at most {DESCRIPTION_MAX} characters."
    return errors


class CreateCategoryController:
    """US-49: a platform manager creates a category. Names are unique, ignoring case."""

    def __init__(self):
        self.entity = CategoryEntity

    def createCategory(self, name, description) -> CategoryEntity:
        name, description = name.strip(), description.strip()
        errors = category_errors(self.entity, name, description)
        if errors:
            raise ValidationError(errors)
        return self.entity.createCategory(name, description)
