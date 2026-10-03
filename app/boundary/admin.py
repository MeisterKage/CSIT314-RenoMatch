from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.boundary.role_tools import CHANGE_PASSWORD, Tool

bp = Blueprint("admin", __name__, url_prefix="/admin")

TOOLS = [
    Tool("User accounts", "Create, view, update, suspend and search accounts.", sprint=1),
    Tool("User profiles", "Group accounts by role and suspend a whole role at once.", sprint=1),
    Tool("Audit log", "See which admin changed which account, and when.", sprint=4),
    Tool("Failed logins", "Spot repeated failed logins and unlock genuine users.", sprint=4),
    Tool("Export accounts", "Download the account list as a CSV file.", sprint=4),
    CHANGE_PASSWORD,
]


class AdminHomePage(MethodView):
    decorators = [role_required("admin")]

    def get(self):
        return render_template("role_home.html", role_label="User Admin", tools=TOOLS)


bp.add_url_rule("/", view_func=AdminHomePage.as_view("home"))
