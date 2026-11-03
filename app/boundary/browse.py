from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.browse_idps_controller import BrowseIDPsController
from app.control.errors import ValidationError
from app.control.rate_review_designer_controller import RateReviewDesignerController
from app.control.save_favourite_controller import SaveFavouriteController
from app.control.search_idps_controller import SearchIDPsController
from app.control.send_enquiry_controller import SendEnquiryController
from app.control.view_designer_profile_controller import ViewDesignerProfileController
from app.control.view_favourites_controller import ViewFavouritesController
from app.control.view_idp_details_controller import ViewIDPDetailsController
from app.entity import CategoryEntity
from app.entity.favourite import NOTE_MAX_LENGTH
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
    """Boundary for US-10 (one IDP with its photos, details and designer link) and US-14.

    US-14 adds the save-favourite form for customers and handles its POST. US-18 adds the
    send-enquiry form and handles its POST.
    """

    def __init__(self):
        self.controller = ViewIDPDetailsController()
        self.saveController = SaveFavouriteController()
        self.favouritesController = ViewFavouritesController()
        self.enquiryController = SendEnquiryController()

    def get(self, idpId):
        viewerId = g.current_account.userId if g.current_account else None
        idp = self.controller.viewIDPDetails(idpId, viewerId)
        if idp is None:
            abort(404)
        return self.displayIDP(idp)

    @role_required("customer")
    def post(self, idpId):
        if request.endpoint == "browse.send_enquiry":
            return self.sendEnquiry(idpId)
        note = request.form.get("note", "").strip()
        goBack = url_for("browse.idp_details", idpId=idpId)
        if request.form.get("next") == "favourites":
            goBack = url_for("favourites.favourites")
        if len(note) > NOTE_MAX_LENGTH:
            flash(f"Keep your note to {NOTE_MAX_LENGTH} characters or fewer.", "danger")
            return redirect(goBack)
        favourite = self.saveController.saveFavourite(g.current_account.userId, idpId, note)
        if favourite is None:
            abort(404)
        return self.displayMessage(goBack)

    def sendEnquiry(self, idpId):
        """US-18: send the enquiry, then show the new thread."""
        try:
            enquiry = self.enquiryController.sendEnquiry(
                g.current_account.userId,
                idpId,
                request.form.get("subject", ""),
                request.form.get("message", ""),
            )
        except ValidationError as error:
            for problem in error.errors.values():
                flash(problem, "danger")
            return redirect(url_for("browse.idp_details", idpId=idpId))
        if enquiry is None:
            abort(404)
        flash("Your enquiry has been sent.", "success")
        return redirect(url_for("enquiries.customer_enquiry", enquiryId=enquiry.enquiryId))

    def displayMessage(self, goBack):
        flash("Saved to your favourites.", "success")
        return redirect(goBack)

    def displayIDP(self, idp):
        favourite = None
        if g.current_account and g.current_account.role == "customer":
            favourite = self.favouritesController.getFavourite(g.current_account.userId, idp.idpId)
        return render_template("browse/idp_details.html", idp=idp, favourite=favourite)


class DesignerProfilePage(MethodView):
    """Boundary for US-11 (a designer's company, portfolio, rating and reviews) and US-19.

    US-19 follows its sequence diagram: `get` on the review route is "click Write a Review"
    (1.1 checkEligibility, then 1.2, 1.3 or 1.4) and `post` is "Submit" (2.1 submitReview,
    then 2.2 or 2.3). The profile controller lives in `profileController` so that
    `controller` is the RateReviewDesignerController, as in the class diagram.

    displayReviewForm takes `existingReview` as sequence step 1.4 draws it (the class
    diagram omits it; the sequence diagram wins). displayMessage takes no argument in
    either diagram, so its text is held in `message`.
    """

    def __init__(self, writeReview=False):
        self.profileController = ViewDesignerProfileController()
        self.controller = RateReviewDesignerController()
        self.writeReview = writeReview
        self.profile = None
        self.message = None
        self.form = {"rating": None, "comment": ""}
        self.showForm = False

    def dispatch_request(self, **kwargs):
        if self.writeReview:
            guarded = role_required("customer")(super().dispatch_request)
            return guarded(**kwargs)
        return super().dispatch_request(**kwargs)

    def get(self, designerId):
        self.profile = self.profileController.viewDesignerProfile(designerId)
        if self.profile is None:
            abort(404)
        if not self.writeReview:
            return self.displayProfile(self.profile)
        userId = g.current_account.userId
        status = self.controller.checkEligibility(designerId, userId)
        if status == "eligible":
            return self.displayReviewForm()
        if status == "not_contacted":
            self.message = "You can only review designers you have contacted"
            return self.displayMessage()
        existingReview = next(
            (review for review in self.profile.reviews if review.userId == userId), None
        )
        return self.displayReviewForm(existingReview)

    def post(self, designerId):
        self.profile = self.profileController.viewDesignerProfile(designerId)
        if self.profile is None:
            abort(404)
        try:
            rating = int(request.form.get("rating", ""))
        except ValueError:
            rating = None
        comment = request.form.get("comment", "")
        self.form = {"rating": rating, "comment": comment}
        if self.controller.submitReview(designerId, g.current_account.userId, rating, comment):
            return self.displayReview()
        self.message = (
            "Your review was not saved. Select a rating and keep your comment "
            "within 1,000 characters"
        )
        self.showForm = True
        return self.displayMessage()

    def displayProfile(self, profile):
        return render_template("browse/designer_profile.html", profile=profile)

    def displayReviewForm(self, existingReview=None):
        """1.2 (no argument) and 1.4: the form, filled with `existingReview` when given."""
        if existingReview is not None:
            self.form = {"rating": existingReview.rating, "comment": existingReview.comment}
        return render_template(
            "browse/designer_profile.html",
            profile=self.profile,
            reviewForm=True,
            form=self.form,
            editing=existingReview is not None,
        )

    def displayReview(self):
        """2.2: the saved review, in the profile's review list with the new average."""
        flash("Your review has been saved.", "success")
        return redirect(
            url_for("browse.designer_profile", designerId=self.profile.designer.userId)
            + "#reviews"
        )

    def displayMessage(self):
        """1.3 and 2.3: `message` above the profile, with the form kept open after 2.3."""
        flash(self.message, "danger")
        return render_template(
            "browse/designer_profile.html",
            profile=self.profile,
            reviewForm=self.showForm,
            form=self.form,
            editing=False,
        )


bp.add_url_rule("/idps", view_func=BrowseIDPsPage.as_view("idps"))
bp.add_url_rule("/idps/<int:idpId>", view_func=IDPDetailsPage.as_view("idp_details"))
bp.add_url_rule(
    "/idps/<int:idpId>/favourite",
    view_func=IDPDetailsPage.as_view("save_favourite"),
    methods=["POST"],
)
bp.add_url_rule(
    "/designers/<int:designerId>",
    view_func=DesignerProfilePage.as_view("designer_profile"),
    methods=["GET"],
)
bp.add_url_rule(
    "/idps/<int:idpId>/enquiry",
    view_func=IDPDetailsPage.as_view("send_enquiry"),
    methods=["POST"],
)
bp.add_url_rule(
    "/designers/<int:designerId>/review",
    view_func=DesignerProfilePage.as_view("review_designer", writeReview=True),
    methods=["GET", "POST"],
)
