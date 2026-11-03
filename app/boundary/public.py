from flask import Blueprint, g, jsonify, render_template
from flask.views import MethodView

from app.control.view_recommended_idps_controller import ViewRecommendedIDPsController
from app.entity import IDPEntity

bp = Blueprint("public", __name__)

NO_RECOMMENDATIONS = "No recommendations yet. Browse IDPs to get personalised suggestions"


class HomePage(MethodView):
    """Boundary for the home page and US-12.

    A logged-in customer follows the US-12 sequence: 1.1 getRecommendedIDPs, then 1.2
    displayRecommendedIDPs, 1.3 displayPopularIDPs (alt 2a) or 1.4 displayMessage (alt 3a).
    Everyone else sees the featured IDPs, read straight from IDPEntity.
    """

    def __init__(self):
        self.controller = ViewRecommendedIDPsController()
        self.recommendedIdps = None
        self.popularIdps = None
        self.featuredIdps = None
        self.message = None

    def get(self):
        account = g.current_account
        if account is None or account.role != "customer":
            self.featuredIdps = IDPEntity.getFeaturedIDPs()
            return self.render()
        recommendations = self.controller.getRecommendedIDPs(account.userId)
        self.recommendedIdps = recommendations.recommendedIdps
        self.popularIdps = recommendations.popularIdps
        if self.recommendedIdps:
            return self.displayRecommendedIDPs()
        if self.popularIdps:
            return self.displayPopularIDPs()
        return self.displayMessage()

    def displayRecommendedIDPs(self):
        """1.2: "Recommended for you" above the style gallery."""
        return self.render()

    def displayPopularIDPs(self):
        """1.3: "Popular designs" for a user with no history."""
        return self.render()

    def displayMessage(self):
        """1.4: the no-recommendations message."""
        self.message = NO_RECOMMENDATIONS
        return self.render()

    def render(self):
        return render_template(
            "public/home.html",
            recommendedIdps=self.recommendedIdps if self.recommendedIdps else None,
            popularIdps=self.popularIdps if self.popularIdps else None,
            featuredIdps=self.featuredIdps,
            recommendationMessage=self.message,
        )


class HealthCheck(MethodView):
    def get(self):
        return jsonify(status="ok")


bp.add_url_rule("/", view_func=HomePage.as_view("home"))
bp.add_url_rule("/health", view_func=HealthCheck.as_view("health"))
