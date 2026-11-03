from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.create_company_info_controller import CreateCompanyInfoController
from app.control.errors import ValidationError
from app.control.update_company_info_controller import UpdateCompanyInfoController
from app.control.view_company_info_controller import ViewCompanyInfoController

bp = Blueprint("company_info", __name__, url_prefix="/designer")

FIELDS = ("name", "description", "address", "phone", "email", "website")


class CompanyInfoPage(MethodView):
    """Boundary for US-35 (create), US-36 (view) and US-37 (update) company information.

    With no record the page shows an empty form that creates it. Otherwise it shows the
    saved details in an edit form.
    """

    decorators = [role_required("designer")]

    def __init__(self):
        self.controller = ViewCompanyInfoController()
        self.createController = CreateCompanyInfoController()
        self.updateController = UpdateCompanyInfoController()

    def get(self):
        company = self.controller.getCompanyInfo(g.current_account.userId)
        form = {field: getattr(company, field) for field in FIELDS} if company else {}
        return self.displayCompanyInfo(form, {}, company is not None)

    def post(self):
        designerId = g.current_account.userId
        form = {field: request.form.get(field, "") for field in FIELDS}
        exists = self.controller.getCompanyInfo(designerId) is not None
        try:
            if exists:
                self.updateController.updateCompanyInfo(designerId, **form)
            else:
                self.createController.createCompanyInfo(designerId, **form)
        except ValidationError as error:
            return self.displayCompanyInfo(form, error.errors, exists)
        flash("Your company information has been saved.", "success")
        return redirect(url_for("company_info.company"))

    def displayCompanyInfo(self, form, errors, exists):
        return render_template(
            "designer/company_info.html", form=form, errors=errors, exists=exists
        )


bp.add_url_rule("/company", view_func=CompanyInfoPage.as_view("company"), methods=["GET", "POST"])
