from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.boundary.role_tools import CHANGE_PASSWORD, Tool

bp = Blueprint("customer", __name__, url_prefix="/customer")

TOOLS = [
    Tool(
        "Search designs",
        "Filter finished projects by style, property and budget.",
        endpoint="browse.idps",
    ),
    Tool(
        "Favourites",
        "Save projects you like, with a note, and compare them later.",
        endpoint="favourites.favourites",
    ),
    Tool(
        "Your details",
        "Keep your name, email and phone number up to date.",
        endpoint="account.account",
    ),
    Tool(
        "Recommended for you",
        "Projects picked from what you have viewed and saved.",
        endpoint="public.home",
    ),
    Tool(
        "Enquiries",
        "Ask a designer about price and availability.",
        endpoint="enquiries.customer_enquiries",
    ),
    Tool(
        "Compare designs",
        "Put up to three projects side by side.",
        endpoint="compare.compare",
    ),
    CHANGE_PASSWORD,
]


class CustomerHomePage(MethodView):
    decorators = [role_required("customer")]

    def get(self):
        return render_template("role_home.html", role_label="Customer", tools=TOOLS)


bp.add_url_rule("/", view_func=CustomerHomePage.as_view("home"))
