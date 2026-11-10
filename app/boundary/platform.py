from flask import Blueprint, redirect, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("platform", __name__, url_prefix="/platform")


class PlatformHomePage(MethodView):
    """Platform managers use the website home page, so this old address sends them there."""

    decorators = [role_required("platform")]

    def get(self):
        return redirect(url_for("public.home"))


bp.add_url_rule("/", view_func=PlatformHomePage.as_view("home"))
