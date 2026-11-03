from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.create_category_controller import CreateCategoryController
from app.control.errors import ValidationError
from app.control.reactivate_category_controller import ReactivateCategoryController
from app.control.search_categories_controller import SearchCategoriesController
from app.control.suspend_category_controller import SuspendCategoryController
from app.control.update_category_controller import UpdateCategoryController
from app.control.view_category_controller import ViewCategoryController
from app.entity.category import CATEGORY_STATUSES

bp = Blueprint("categories", __name__, url_prefix="/platform/categories")

NO_MATCH = "No categories match your search."


class ManageCategoriesPage(MethodView):
    """Boundary for US-50 (view), US-52 (suspend), US-53 (reactivate) and US-54 (search).

    `controller` is the US-54 class diagram's SearchCategoriesController, so the other
    controllers use their own attribute names. The display methods take no argument, as in the
    class diagram, so the page holds what they show in `categories`, `message` and `filters`.
    """

    decorators = [role_required("platform")]

    def __init__(self):
        self.controller = SearchCategoriesController()
        self.viewController = ViewCategoryController()
        self.suspendController = SuspendCategoryController()
        self.reactivateController = ReactivateCategoryController()
        self.categories = []
        self.message = None
        self.filters = {"keyword": "", "status": ""}

    def get(self, categoryId=None):
        if categoryId is not None:
            return self.displayCategory(categoryId)
        # 1: enter keyword, click "Search"
        keyword = request.args.get("keyword", "").strip()
        status = request.args.get("status", "").strip()
        if status not in CATEGORY_STATUSES:
            status = ""
        self.filters = {"keyword": keyword, "status": status}
        categories = self.controller.searchCategories(keyword, status)  # 1.1
        if categories:  # [categories not empty]
            self.categories = categories
            return self.displayCategories()  # 1.2
        self.message = NO_MATCH  # [3a. no category found]
        return self.displayMessage()  # 1.3

    def post(self, categoryId):
        if request.endpoint == "categories.category_suspend":
            action, done = self.suspendController.suspendCategory, "Category suspended."
        else:
            action, done = self.reactivateController.reactivateCategory, "Category reactivated."
        try:
            action(categoryId)
        except ValidationError as error:
            flash(str(error), "danger")
        else:
            flash(done, "success")
        return redirect(self.nextUrl())

    @staticmethod
    def nextUrl() -> str:
        """Back to the page the button was on: a path under /platform/categories, else the list."""
        target = request.form.get("next", "")
        if target.startswith("/platform/categories") and "//" not in target and "\\" not in target:
            return target
        return url_for("categories.categories")

    def displayCategories(self):
        return render_template(
            "platform/categories.html",
            categories=self.categories,
            filters=self.filters,
            message=None,
            statuses=CATEGORY_STATUSES,
        )

    def displayMessage(self):
        return render_template(
            "platform/categories.html",
            categories=[],
            filters=self.filters,
            message=self.message,
            statuses=CATEGORY_STATUSES,
        )

    def displayCategory(self, categoryId):
        category = self.viewController.getCategory(categoryId)
        if category is None:
            abort(404)
        return render_template("platform/category_view.html", category=category)


class CategoryFormPage(MethodView):
    """Boundary for US-49 (create) and US-51 (update)."""

    decorators = [role_required("platform")]

    def __init__(self):
        self.createController = CreateCategoryController()
        self.updateController = UpdateCategoryController()
        self.viewController = ViewCategoryController()

    def get(self, categoryId=None):
        if categoryId is None:
            return self.displayForm(None, {"name": "", "description": ""}, {})
        category = self.viewController.getCategory(categoryId)
        if category is None:
            abort(404)
        form = {"name": category.name, "description": category.description}
        return self.displayForm(category, form, {})

    def post(self, categoryId=None):
        form = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
        }
        category = None
        if categoryId is not None:
            category = self.viewController.getCategory(categoryId)
            if category is None:
                abort(404)
        try:
            if category is None:
                category = self.createController.createCategory(form["name"], form["description"])
                done = "Category created."
            else:
                self.updateController.updateCategory(categoryId, form["name"], form["description"])
                done = "Category updated."
        except ValidationError as error:
            return self.displayForm(category, form, error.errors)
        flash(done, "success")
        return redirect(url_for("categories.category_view", categoryId=category.categoryId))

    def displayForm(self, category, form, errors):
        return render_template(
            "platform/category_form.html", category=category, form=form, errors=errors
        )


bp.add_url_rule("", view_func=ManageCategoriesPage.as_view("categories"))
bp.add_url_rule("/new", view_func=CategoryFormPage.as_view("category_new"))
bp.add_url_rule("/<int:categoryId>", view_func=ManageCategoriesPage.as_view("category_view"))
bp.add_url_rule(
    "/<int:categoryId>/edit", view_func=CategoryFormPage.as_view("category_edit")
)
bp.add_url_rule(
    "/<int:categoryId>/suspend",
    view_func=ManageCategoriesPage.as_view("category_suspend"),
    methods=["POST"],
)
bp.add_url_rule(
    "/<int:categoryId>/reactivate",
    view_func=ManageCategoriesPage.as_view("category_reactivate"),
    methods=["POST"],
)
