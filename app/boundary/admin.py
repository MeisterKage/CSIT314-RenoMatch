from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


class AdminHomePage(MethodView):
    decorators = [role_required("admin")]

    def get(self):
        return render_template("role_home.html", role_label="User Admin")


bp.add_url_rule("/", view_func=AdminHomePage.as_view("home"))
