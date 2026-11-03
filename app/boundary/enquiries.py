from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import login_required
from app.control.errors import ValidationError
from app.control.reply_enquiry_controller import ReplyEnquiryController
from app.control.view_enquiries_controller import ViewEnquiriesController

bp = Blueprint("enquiries", __name__)


class EnquiriesPage(MethodView):
    """Boundary for US-47 (a designer's inbox and replies) and the customer's own threads.

    The designer routes are /designer/enquiries and the customer routes are /enquiries.
    Both use the same controllers, through their designer-side and customer-side methods.
    """

    decorators = [login_required]

    def __init__(self, role):
        self.role = role
        self.controller = ViewEnquiriesController()
        self.replyController = ReplyEnquiryController()

    def dispatch_request(self, **kwargs):
        if g.current_account.role != self.role:
            abort(403)
        return super().dispatch_request(**kwargs)

    def get(self, enquiryId=None):
        userId = g.current_account.userId
        if enquiryId is None:
            if self.role == "designer":
                return self.displayEnquiries(self.controller.getEnquiries(userId))
            return self.displayEnquiries(self.controller.getCustomerEnquiries(userId))
        if self.role == "designer":
            enquiry = self.controller.getEnquiryThread(enquiryId, userId)
        else:
            enquiry = self.controller.getCustomerEnquiryThread(enquiryId, userId)
        if enquiry is None:
            abort(404)
        return self.displayThread(enquiry)

    def post(self, enquiryId):
        userId = g.current_account.userId
        body = request.form.get("body", "")
        try:
            if self.role == "designer":
                message = self.replyController.replyEnquiry(enquiryId, userId, body)
            else:
                message = self.replyController.replyAsCustomer(enquiryId, userId, body)
        except ValidationError as error:
            for problem in error.errors.values():
                flash(problem, "danger")
            return redirect(self.threadUrl(enquiryId))
        if message is None:
            abort(404)
        flash("Your reply has been sent.", "success")
        return redirect(self.threadUrl(enquiryId))

    def threadUrl(self, enquiryId):
        endpoint = "designer_enquiry" if self.role == "designer" else "customer_enquiry"
        return url_for(f"enquiries.{endpoint}", enquiryId=enquiryId)

    def displayEnquiries(self, enquiries):
        return render_template(
            "enquiries/enquiries.html",
            enquiries=enquiries,
            role=self.role,
            threadEndpoint=f"enquiries.{self.role}_enquiry",
        )

    def displayThread(self, enquiry):
        return render_template("enquiries/thread.html", enquiry=enquiry, role=self.role)


bp.add_url_rule(
    "/designer/enquiries",
    view_func=EnquiriesPage.as_view("designer_enquiries", role="designer"),
    methods=["GET"],
)
bp.add_url_rule(
    "/designer/enquiries/<int:enquiryId>",
    view_func=EnquiriesPage.as_view("designer_enquiry", role="designer"),
    methods=["GET", "POST"],
)
bp.add_url_rule(
    "/enquiries",
    view_func=EnquiriesPage.as_view("customer_enquiries", role="customer"),
    methods=["GET"],
)
bp.add_url_rule(
    "/enquiries/<int:enquiryId>",
    view_func=EnquiriesPage.as_view("customer_enquiry", role="customer"),
    methods=["GET", "POST"],
)
