from flask import Blueprint, g, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.view_interest_dashboard_controller import ViewInterestDashboardController

bp = Blueprint("interest", __name__, url_prefix="/designer")


class InterestDashboardPage(MethodView):
    """Boundary for US-46: views and shortlists per style and category, and the top IDPs."""

    decorators = [role_required("designer")]

    def __init__(self):
        self.controller = ViewInterestDashboardController()

    def get(self):
        dashboard = self.controller.getInterestDashboard(g.current_account.userId)
        return self.displayDashboard(dashboard)

    def displayDashboard(self, dashboard):
        return render_template("designer/dashboard.html", dashboard=dashboard)


bp.add_url_rule("/dashboard", view_func=InterestDashboardPage.as_view("dashboard"))
