from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import login_required
from app.control.delete_account_controller import DeleteAccountController
from app.control.errors import ValidationError
from app.control.logout_controller import LogoutController
from app.control.update_account_details_controller import UpdateAccountDetailsController

bp = Blueprint("account", __name__)


class MyAccountPage(MethodView):
    """Boundary for US-07 and US-08, for every role: update own details, the designer's
    weekly summary opt-in, and delete own account."""

    decorators = [login_required]

    def __init__(self):
        self.updateController = UpdateAccountDetailsController()
        self.deleteController = DeleteAccountController()

    def current(self) -> dict:
        account = g.current_account
        return {"name": account.name, "email": account.email, "phone": account.phone}

    def get(self):
        return render_template("account.html", form=self.current(), errors={})

    def post(self):
        endpoint = request.endpoint
        if endpoint == "account.weekly_summary":
            return self.setWeeklySummary()
        if endpoint == "account.delete":
            return self.deleteAccount()
        return self.updateDetails()

    def updateDetails(self):
        form = {key: request.form.get(key, "") for key in ("name", "email", "phone")}
        try:
            self.updateController.updateAccountDetails(g.current_account.userId, **form)
        except ValidationError as error:
            return render_template("account.html", form=form, errors=error.errors)
        return render_template(
            "account.html",
            form=self.current(),
            errors={},
            notice="Your details have been updated.",
        )

    def setWeeklySummary(self):
        if g.current_account.role != "designer":
            abort(403)
        self.updateController.setWeeklySummaryOptIn(
            g.current_account.userId, request.form.get("optIn") == "on"
        )
        flash("Weekly summary preference saved.", "success")
        return redirect(url_for("account.account"))

    def deleteAccount(self):
        account = g.current_account
        errors = {}
        if request.form.get("confirmUsername", "").strip().lower() != account.username:
            errors["confirmUsername"] = "Type your username to confirm."
        else:
            try:
                password = request.form.get("password", "")
                self.deleteController.deleteAccount(account.userId, password)
            except ValidationError as error:
                errors = error.errors
        if errors:
            return render_template(
                "account.html", form=self.current(), errors={}, delete_errors=errors
            )
        LogoutController().logout(session)
        flash("Your account has been deleted.", "info")
        return redirect(url_for("public.home"))


bp.add_url_rule("/account", view_func=MyAccountPage.as_view("account"), methods=["GET", "POST"])
bp.add_url_rule(
    "/account/weekly-summary",
    view_func=MyAccountPage.as_view("weekly_summary"),
    methods=["POST"],
)
bp.add_url_rule("/account/delete", view_func=MyAccountPage.as_view("delete"), methods=["POST"])
