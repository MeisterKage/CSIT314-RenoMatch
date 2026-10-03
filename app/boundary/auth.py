from flask import Blueprint, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError
from app.control.login_controller import LoginController

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


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
