from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.add_idp_controller import AddIDPController
from app.control.delete_idp_controller import DeleteIDPController
from app.control.search_my_idps_controller import SearchMyIDPsController
from app.control.update_idp_controller import UpdateIDPController
from app.control.view_company_info_controller import ViewCompanyInfoController
from app.control.view_my_idp_controller import ViewMyIDPController
from app.entity import CategoryEntity
from app.entity.idp import IDP_STAGES, PROPERTY_TYPES, STYLES

bp = Blueprint("portfolio", __name__, url_prefix="/designer/portfolio")

FORM_FIELDS = (
    "title",
    "description",
    "categoryId",
    "style",
    "propertyType",
    "budget",
    "location",
    "stage",
)
FIELD_LABELS = {
    "title": "Title",
    "description": "Description",
    "categoryId": "Category",
    "style": "Style",
    "propertyType": "Property type",
    "budget": "Budget",
    "location": "Location",
    "stage": "Stage",
    "photos": "Photos",
}
SUCCESS_ADDED = "Your project has been added."
SUCCESS_UPDATED = "Your project has been updated."
SUCCESS_REMOVED = "Your project has been removed from your portfolio."
CATEGORY_SUSPENDED = "That category is suspended. Please choose another category."
COMPANY_REQUIRED = "Add your company information before you add a project."


def missingFieldsMessage(missingFields):
    labels = ", ".join(FIELD_LABELS[name] for name in missingFields)
    return f"Please fill in all required fields correctly: {labels}."


def readForm():
    """The form fields of the add and edit pages as a dict, plus the photos to remove."""
    idp = {name: request.form.get(name, "") for name in FORM_FIELDS}
    idp["removePhotos"] = request.form.getlist("removePhotos")
    return idp


def readPhotos():
    """The uploaded photos. A browser sends one empty part when no file was chosen."""
    return [photo for photo in request.files.getlist("photos") if photo.filename]


class MyPortfolioPage(MethodView):
    """Boundary for US-38 (Add IDP, with US-45 photos) and US-42 (search own IDPs).

    `/designer/portfolio` lists the designer's IDPs. `/designer/portfolio/new` is the add form.
    In the US-38 sequence `post` is step 1 (enter details, upload photos, click "Save"). The
    display methods take no argument, as in the class diagram, so the page holds what they
    show in `form`, `message` and `errors`.
    """

    decorators = [role_required("designer")]

    def __init__(self, showForm=False):
        self.showForm = showForm
        self.controller = AddIDPController()
        self.searchController = SearchMyIDPsController()
        self.companyController = ViewCompanyInfoController()
        self.form = {}
        self.message = None
        self.errors = {}

    def get(self):
        if not self.showForm:
            keyword = request.args.get("keyword", "").strip()
            idps = self.searchController.searchMyIDPs(g.current_account.userId, keyword)
            return render_template("designer/portfolio.html", idps=idps, keyword=keyword)
        if not self.hasCompanyInfo():
            return self.displayCompanyRequired()
        return self.displayAddIDPForm()

    def post(self):
        designerId = g.current_account.userId
        if not self.hasCompanyInfo():
            return self.displayCompanyRequired()
        self.form = readForm()
        idp = {**self.form, "designerId": designerId}
        result = self.controller.addIDP(idp, readPhotos())  # 1.1
        if isinstance(result, bool):  # [details and photos valid]
            if result:  # [result = true]
                return self.displaySuccess()  # 1.2
            self.message = CATEGORY_SUSPENDED  # [6c. category suspended]
            self.errors = {"categoryId": "Choose another category."}
            return self.displayMessage()  # 1.3
        if isinstance(result, list):  # [6a. required fields missing] missingFields
            self.message = missingFieldsMessage(result)
            self.errors = {name: "Check this field." for name in result}
            return self.displayMessage()  # 1.4
        self.message = result  # [6b. photo not JPG/PNG or over 5 MB] invalidPhoto
        self.errors = {"photos": "Choose JPG or PNG photos of 5 MB or less."}
        return self.displayMessage()  # 1.5

    def hasCompanyInfo(self):
        return self.companyController.getCompanyInfo(g.current_account.userId) is not None

    def displayAddIDPForm(self):
        return render_template(
            "designer/idp_form.html",
            form=self.form,
            errors=self.errors,
            message=self.message,
            **formChoices(),
        )

    def displaySuccess(self):
        flash(SUCCESS_ADDED, "success")
        return redirect(url_for("portfolio.portfolio"))

    def displayMessage(self):
        return self.displayAddIDPForm()

    def displayCompanyRequired(self):
        return render_template(
            "designer/idp_form.html", needsCompany=True, message=COMPANY_REQUIRED
        )


class MyIDPDetailsPage(MethodView):
    """Boundary for US-39 (view own IDP) and US-41 (delete own IDP).

    The controllers are held as `viewMyIDPController` and `deleteController`, leaving
    `controller` free for the view count controller of US-43.
    """

    decorators = [role_required("designer")]

    def __init__(self):
        self.viewMyIDPController = ViewMyIDPController()
        self.deleteController = DeleteIDPController()
        self.message = None

    def get(self, idpId):
        idp = self.viewMyIDPController.getMyIDP(g.current_account.userId, idpId)
        if idp is None:
            abort(404)
        return self.displayIDP(idp)

    def post(self, idpId):
        """Delete: POST /designer/portfolio/<idpId>/delete."""
        if not self.deleteController.deleteIDP(g.current_account.userId, idpId):
            abort(404)
        self.message = SUCCESS_REMOVED
        return self.displayMessage()

    def displayIDP(self, idp):
        return render_template("designer/my_idp.html", idp=idp)

    def displayMessage(self):
        flash(self.message, "success")
        return redirect(url_for("portfolio.portfolio"))


class EditIDPPage(MethodView):
    """Boundary for US-40: change an IDP and add or remove its photos (US-45)."""

    decorators = [role_required("designer")]

    def __init__(self):
        self.controller = UpdateIDPController()
        self.viewMyIDPController = ViewMyIDPController()
        self.message = None
        self.errors = {}

    def get(self, idpId):
        idp = self.viewMyIDPController.getMyIDP(g.current_account.userId, idpId)
        if idp is None:
            abort(404)
        form = {name: getattr(idp, name) for name in FORM_FIELDS}
        return self.displayEditForm(idp, form)

    def post(self, idpId):
        designerId = g.current_account.userId
        form = readForm()
        result = self.controller.updateIDP(designerId, idpId, form, readPhotos())
        if result is None:
            abort(404)
        if result is True:
            flash(SUCCESS_UPDATED, "success")
            return redirect(url_for("portfolio.idp_details", idpId=idpId))
        if result is False:
            self.message = CATEGORY_SUSPENDED
            self.errors = {"categoryId": "Choose another category."}
        elif isinstance(result, list):
            self.message = missingFieldsMessage(result)
            self.errors = {name: "Check this field." for name in result}
        else:
            self.message = result
            self.errors = {"photos": "Choose JPG or PNG photos of 5 MB or less."}
        idp = self.viewMyIDPController.getMyIDP(designerId, idpId)
        return self.displayEditForm(idp, form)

    def displayEditForm(self, idp, form):
        return render_template(
            "designer/idp_form.html",
            form=form,
            errors=self.errors,
            message=self.message,
            idp=idp,
            **formChoices(idp),
        )


def formChoices(idp=None):
    """Options for the add and edit forms. An edited IDP keeps its own category in the list
    even when that category has since been suspended."""
    categories = CategoryEntity.getActiveCategories()
    if idp is not None and idp.category not in categories:
        categories.append(idp.category)
    return {
        "categories": categories,
        "styles": STYLES,
        "propertyTypes": PROPERTY_TYPES,
        "stages": IDP_STAGES,
    }


bp.add_url_rule("", view_func=MyPortfolioPage.as_view("portfolio"), methods=["GET"])
bp.add_url_rule(
    "/new", view_func=MyPortfolioPage.as_view("new_idp", showForm=True), methods=["GET", "POST"]
)
bp.add_url_rule(
    "/<int:idpId>", view_func=MyIDPDetailsPage.as_view("idp_details"), methods=["GET"]
)
bp.add_url_rule(
    "/<int:idpId>/delete", view_func=MyIDPDetailsPage.as_view("delete_idp"), methods=["POST"]
)
bp.add_url_rule(
    "/<int:idpId>/edit", view_func=EditIDPPage.as_view("edit_idp"), methods=["GET", "POST"]
)
