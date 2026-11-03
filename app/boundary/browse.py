from flask import Blueprint, abort, flash, g, render_template, request
from flask.views import MethodView

from app.control.browse_idps_controller import BrowseIDPsController
from app.control.search_idps_controller import SearchIDPsController
from app.control.view_designer_profile_controller import ViewDesignerProfileController
from app.control.view_idp_details_controller import ViewIDPDetailsController
from app.entity import CategoryEntity
from app.entity.idp import PROPERTY_TYPES, STYLES

bp = Blueprint("browse", __name__)


def parse_positive_int(text, default=None):
    try:
        value = int(text)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def parse_budget(text):
    """A non-negative number, or None when blank. Raises ValueError for anything else."""
    text = (text or "").strip()
    if not text:
        return None
    value = float(text.replace(",", ""))
    if value != value or value < 0 or value == float("inf"):
        raise ValueError(text)
    return value


class BrowseIDPsPage(MethodView):
    """Boundary for US-01 (browse) and US-09 (search): the photo-card grid of Active IDPs."""

    def __init__(self):
        self.controller = BrowseIDPsController()
        self.searchController = SearchIDPsController()

    def get(self):
        args = request.args
        filters = {
            "keyword": args.get("keyword", "").strip(),
            "category": args.get("category", "").strip(),
            "style": args.get("style", "").strip(),
            "propertyType": args.get("propertyType", "").strip(),
            "minBudget": args.get("minBudget", "").strip(),
            "maxBudget": args.get("maxBudget", "").strip(),
        }
        page = parse_positive_int(args.get("page"), 1)
        try:
            minBudget = parse_budget(filters["minBudget"])
            maxBudget = parse_budget(filters["maxBudget"])
        except ValueError:
            flash("Enter budgets as numbers, for example 30000.", "danger")
            minBudget = maxBudget = None
            filters["minBudget"] = filters["maxBudget"] = ""
        if minBudget is not None and maxBudget is not None and minBudget > maxBudget:
            flash("Minimum budget cannot be above the maximum.", "danger")
            minBudget = maxBudget = None
            filters["minBudget"] = filters["maxBudget"] = ""
        categoryId = parse_positive_int(filters["category"])
        if any(filters.values()):
            results = self.searchController.searchIDPs(
                filters["keyword"],
                categoryId,
                filters["style"],
                filters["propertyType"],
                minBudget,
                maxBudget,
                page,
            )
        else:
            results = self.controller.getActiveIDPs(page)
        return self.displayIDPs(results, filters, categoryId)

    def displayIDPs(self, results, filters, categoryId):
        return render_template(
            "browse/idps.html",
            results=results,
            filters=filters,
            selectedCategory=categoryId,
            categories=CategoryEntity.getActiveCategories(),
            styles=STYLES,
            propertyTypes=PROPERTY_TYPES,
            pageArgs={key: value for key, value in filters.items() if value},
        )


class IDPDetailsPage(MethodView):
    """Boundary for US-10: one IDP with its photos, details and designer link.

    US-14 (save favourite) and US-18 (send enquiry) add their forms to this page.
    """

    def __init__(self):
        self.controller = ViewIDPDetailsController()

    def get(self, idpId):
        viewerId = g.current_account.userId if g.current_account else None
        idp = self.controller.viewIDPDetails(idpId, viewerId)
        if idp is None:
            abort(404)
        return self.displayIDP(idp)

    def displayIDP(self, idp):
        return render_template("browse/idp_details.html", idp=idp)


class DesignerProfilePage(MethodView):
    """Boundary for US-11: a designer's company, portfolio, rating and reviews.

    US-19 adds RateReviewDesignerController and its displayReviewForm(), displayReview()
    and displayMessage() to this page. It will set `controller` to that controller, so
    the profile controller lives in `profileController`.
    """

    def __init__(self):
        self.profileController = ViewDesignerProfileController()

    def get(self, designerId):
        profile = self.profileController.viewDesignerProfile(designerId)
        if profile is None:
            abort(404)
        return self.displayProfile(profile)

    def displayProfile(self, profile):
        return render_template("browse/designer_profile.html", profile=profile)


bp.add_url_rule("/idps", view_func=BrowseIDPsPage.as_view("idps"))
bp.add_url_rule("/idps/<int:idpId>", view_func=IDPDetailsPage.as_view("idp_details"))
bp.add_url_rule(
    "/designers/<int:designerId>", view_func=DesignerProfilePage.as_view("designer_profile")
)
