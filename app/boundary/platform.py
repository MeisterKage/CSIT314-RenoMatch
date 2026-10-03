from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("platform", __name__, url_prefix="/platform")


class PlatformHomePage(MethodView):
    decorators = [role_required("platform")]

    def get(self):
        return render_template("role_home.html", role_label="Platform Management")


bp.add_url_rule("/", view_func=PlatformHomePage.as_view("home"))
