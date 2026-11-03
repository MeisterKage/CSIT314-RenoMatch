"""Platform manager pages: US-60 (Feature IDPs on Home Page) and US-58 (Review Reported IDPs)."""

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.feature_idp_controller import FeatureIDPController
from app.control.resolve_reported_idp_controller import ResolveReportedIDPController
from app.control.view_featured_idps_controller import ViewFeaturedIDPsController
from app.control.view_reported_idps_controller import ViewReportedIDPsController

bp = Blueprint("moderation", __name__, url_prefix="/platform")

SUCCESS_FEATURED = "The IDP is now featured on the home page."
SUCCESS_UNFEATURED = "The IDP is no longer featured on the home page."
LIMIT_REACHED = "Maximum of 6 featured IDPs. Unfeature one first"
NOT_ACTIVE = "That IDP is suspended or removed, so it cannot be featured."
NOT_UNFEATURED = "That IDP could not be unfeatured."
REPORT_UPHELD = "Report upheld. The IDP has been removed."
REPORT_DISMISSED = "Report dismissed. The IDP stays on the site."
REPORT_CLOSED = "That report was already resolved."
FEATURED_SLOTS = 6


def safeNext(default, prefix):
    """The page to return to after a post, only when it is on the same section of the site."""
    target = request.form.get("next", "")
    return target if target.startswith(prefix) and "//" not in target else default


class ManageFeaturedIDPsPage(MethodView):
    """Boundary for US-60. In the sequence `post` is step 1 (select IDP, click "Feature") or
    step 2 (click "Unfeature"). `displaySuccess` and `displayMessage` take no argument, as in
    the class diagram, so the page holds what they show in `message`."""

    decorators = [role_required("platform")]

    def __init__(self):
        self.controller = FeatureIDPController()
        self.viewController = ViewFeaturedIDPsController()
        self.message = None

    def get(self):
        return self.displayFeaturedIDPs()

    def post(self, idpId):
        if request.endpoint == "moderation.featured_unfeature":
            return self.unfeature(idpId)
        result = self.controller.featureIDP(idpId)  # 1.1
        if result:  # [count < 6] [result = true]
            self.message = SUCCESS_FEATURED
            return self.displaySuccess()  # 1.2
        if self.controller.limitReached:  # [4a. 6 IDPs already featured]
            self.message = LIMIT_REACHED
            return self.displayMessage()  # 1.4
        self.message = NOT_ACTIVE  # [5a. IDP suspended or removed]
        return self.displayMessage()  # 1.3

    def unfeature(self, idpId):
        """[3a. unfeature a featured IDP] step 2 onwards."""
        if self.controller.unfeatureIDP(idpId):  # 2.1
            self.message = SUCCESS_UNFEATURED
            return self.displaySuccess()  # 2.2
        self.message = NOT_UNFEATURED
        return self.displayMessage()

    def displayFeaturedIDPs(self):
        keyword = request.args.get("keyword", "").strip()
        try:
            number = max(1, int(request.args.get("page", "1")))
        except ValueError:
            number = 1
        return render_template(
            "platform/featured.html",
            featured=self.viewController.getFeaturedIDPs(),
            pagination=self.viewController.searchActiveIDPs(keyword, number),
            keyword=keyword,
            pageArgs={"keyword": keyword} if keyword else {},
            slots=FEATURED_SLOTS,
        )

    def displaySuccess(self):
        flash(self.message, "success")
        return redirect(safeNext(url_for("moderation.featured"), "/platform/featured"))

    def displayMessage(self):
        flash(self.message, "danger")
        return redirect(safeNext(url_for("moderation.featured"), "/platform/featured"))


class ReportedIDPsPage(MethodView):
    """Boundary for US-58: Open reports with the IDP and reason, to uphold or dismiss."""

    decorators = [role_required("platform")]

    def __init__(self):
        self.viewController = ViewReportedIDPsController()
        self.resolveController = ResolveReportedIDPController()

    def get(self):
        reports = self.viewController.getOpenReports()
        return render_template("platform/reported.html", reports=reports)

    def post(self, flagId):
        decision = "uphold" if request.endpoint == "moderation.reported_uphold" else "dismiss"
        if not self.resolveController.resolveReport(flagId, g.current_account.userId, decision):
            flash(REPORT_CLOSED, "danger")
        elif decision == "uphold":
            flash(REPORT_UPHELD, "success")
        else:
            flash(REPORT_DISMISSED, "success")
        return redirect(url_for("moderation.reported"))


bp.add_url_rule("/featured", view_func=ManageFeaturedIDPsPage.as_view("featured"))
bp.add_url_rule(
    "/featured/<int:idpId>/feature",
    view_func=ManageFeaturedIDPsPage.as_view("featured_feature"),
    methods=["POST"],
)
bp.add_url_rule(
    "/featured/<int:idpId>/unfeature",
    view_func=ManageFeaturedIDPsPage.as_view("featured_unfeature"),
    methods=["POST"],
)
bp.add_url_rule("/reported", view_func=ReportedIDPsPage.as_view("reported"))
bp.add_url_rule(
    "/reported/<int:flagId>/uphold",
    view_func=ReportedIDPsPage.as_view("reported_uphold"),
    methods=["POST"],
)
bp.add_url_rule(
    "/reported/<int:flagId>/dismiss",
    view_func=ReportedIDPsPage.as_view("reported_dismiss"),
    methods=["POST"],
)
