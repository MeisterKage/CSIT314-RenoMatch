from flask import Blueprint, redirect, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("customer", __name__, url_prefix="/customer")


class CustomerHomePage(MethodView):
    """Customers use the website home page, so this old address sends them there."""

    decorators = [role_required("customer")]

    def get(self):
        return redirect(url_for("public.home"))


bp.add_url_rule("/", view_func=CustomerHomePage.as_view("home"))
