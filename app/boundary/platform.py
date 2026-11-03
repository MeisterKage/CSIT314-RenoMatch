from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.boundary.role_tools import CHANGE_PASSWORD, Tool

bp = Blueprint("platform", __name__, url_prefix="/platform")

TOOLS = [
    Tool(
        "Project categories",
        "Create, update, suspend and search project categories.",
        sprint=2,
        endpoint="categories.categories",
    ),
    Tool(
        "Activity reports",
        "Daily, monthly and custom-range activity, with a PDF export.",
        sprint=3,
        endpoint="reports.reports",
    ),
    Tool("Featured projects", "Choose which projects appear on the home page.", sprint=4),
    Tool("Reported projects", "Review projects users have reported and remove bad ones.", sprint=5),
    CHANGE_PASSWORD,
]


class PlatformHomePage(MethodView):
    decorators = [role_required("platform")]

    def get(self):
        return render_template("role_home.html", role_label="Platform Management", tools=TOOLS)


bp.add_url_rule("/", view_func=PlatformHomePage.as_view("home"))
