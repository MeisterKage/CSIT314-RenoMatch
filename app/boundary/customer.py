from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("customer", __name__, url_prefix="/customer")


class CustomerHomePage(MethodView):
    decorators = [role_required("customer")]

    def get(self):
        return render_template("role_home.html", role_label="Customer")


bp.add_url_rule("/", view_func=CustomerHomePage.as_view("home"))
