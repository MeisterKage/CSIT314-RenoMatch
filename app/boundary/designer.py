from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.boundary.role_tools import CHANGE_PASSWORD, Tool

bp = Blueprint("designer", __name__, url_prefix="/designer")

TOOLS = [
    Tool(
        "Company information",
        "Tell homeowners about your studio and how to reach it.",
        endpoint="company_info.company",
    ),
    Tool(
        "Portfolio projects",
        "Add current and past projects with photos and budgets.",
        endpoint="portfolio.portfolio",
    ),
    Tool(
        "Project interest",
        "See how often each project is viewed and shortlisted.",
        endpoint="portfolio.portfolio",
    ),
    Tool(
        "Interest dashboard",
        "See which styles and categories draw the most interest.",
        endpoint="interest.dashboard",
    ),
    Tool(
        "Enquiries",
        "Read and reply to homeowners' questions.",
        endpoint="enquiries.designer_enquiries",
    ),
    Tool(
        "Weekly summary",
        "Get your views and shortlists by email each week.",
        endpoint="account.account",
    ),
    CHANGE_PASSWORD,
]


class DesignerHomePage(MethodView):
    decorators = [role_required("designer")]

    def get(self):
        return render_template("role_home.html", role_label="Interior Designer", tools=TOOLS)


bp.add_url_rule("/", view_func=DesignerHomePage.as_view("home"))
