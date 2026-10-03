from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError
from app.control.login_controller import LoginController
from app.control.logout_controller import LogoutController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_current_account)


@bp.app_context_processor
def inject_role_home():
    return {"ROLE_HOME": ROLE_HOME}


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


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
bp.add_url_rule("/logout", view_func=LogoutAction.as_view("logout"))
