from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError, ValidationError
from app.control.login_controller import LoginController
from app.control.logout_controller import LogoutController
from app.control.register_controller import RegisterController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_current_account)


@bp.app_context_processor
def inject_role_home():
    return {"ROLE_HOME": ROLE_HOME}


def _without_passwords(form: dict) -> dict:
    return {key: value for key, value in form.items() if "password" not in key}


class LoginPage(MethodView):
    """Boundary for US01: log in."""

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/login.html")

    def post(self):
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            account = LoginController().login(username, password)
        except LoginError as error:
            return render_template("auth/login.html", error=str(error), username=username)
        session.clear()
        session["account_id"] = account.id
        return redirect(url_for(ROLE_HOME[account.role]))


class LogoutAction(MethodView):
    """Boundary for US02: log out."""

    def post(self):
        LogoutController().logout(session)
        flash("You have been logged out.", "info")
        return redirect(url_for("public.home"))


class RegisterPage(MethodView):
    """Boundary for US03: register as a customer or interior designer."""

    FIELDS = ("username", "email", "password", "confirm_password", "full_name", "phone", "role")

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/register.html", form={}, errors={})

    def post(self):
        form = {field: request.form.get(field, "") for field in self.FIELDS}
        try:
            RegisterController().register(**form)
        except ValidationError as error:
            return render_template(
                "auth/register.html", form=_without_passwords(form), errors=error.errors
            )
        flash("Account created. You can log in now.", "success")
        return redirect(url_for("auth.login"))


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
bp.add_url_rule("/logout", view_func=LogoutAction.as_view("logout"))
bp.add_url_rule("/register", view_func=RegisterPage.as_view("register"))
