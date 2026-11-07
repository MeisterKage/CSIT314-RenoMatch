from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.compare_idps_controller import CompareIDPsController

bp = Blueprint("compare", __name__)

MAX_SELECTED = 3
MIN_SELECTED = 2
TOO_MANY = "You can compare up to 3 IDPs"
TOO_FEW = "Select at least 2 IDPs to compare"
UNAVAILABLE = "One IDP is no longer available"


def backTo() -> str:
    """The page the user ticked from (path only), else the comparison page."""
    path = urlparse(request.referrer or "").path
    if path.startswith("/") and not path.startswith("//") and "\\" not in path:
        return path
    return url_for("compare.compare")


def selectedIds() -> list[int]:
    return list(session.get("compareIds", []))


@bp.app_context_processor
def injectCompareCount():
    return {"compareCount": len(selectedIds())}


class CompareIDPPage(MethodView):
    """Boundary for US-13. The selection of up to 3 IDP ids is kept in the session.

    `post` on /compare/select is sequence step 1 (tick "Compare" on an IDP), with
    1.1 displayMessage() when 3 are already selected (opt 1a). `get` on /compare is step 2
    (click "Compare"): 2.1 compareIDPs, then 2.2 displayComparison, or 2.4 displayMessage
    (alt 2a), and 2.3 displayMessage when a selected IDP is no longer available (opt 3a).
    Both display methods take no argument, as in the class diagram, so the data they show
    is held in `idps` and `message`.
    """

    decorators = [role_required("customer")]

    def __init__(self):
        self.controller = CompareIDPsController()
        self.idps = []
        self.message = None

    def get(self):
        idpIds = selectedIds()
        self.idps = self.controller.compareIDPs(idpIds)
        if len(idpIds) < MIN_SELECTED:
            self.message = TOO_FEW
            self.idps = []
            self.displayMessage()
        elif len(self.idps) < len(idpIds):
            session["compareIds"] = [idp.idpId for idp in self.idps]
            self.displayComparison()
            self.message = UNAVAILABLE
            self.displayMessage()
        else:
            self.displayComparison()
        return self.render()

    def post(self):
        if request.endpoint == "compare.clear":
            session["compareIds"] = []
            return redirect(url_for("compare.compare"))
        try:
            idpId = int(request.form.get("idpId", ""))
        except ValueError:
            return redirect(url_for("browse.idps"))
        idpIds = selectedIds()
        if idpId not in idpIds:
            if len(idpIds) >= MAX_SELECTED:
                self.message = TOO_MANY
                self.displayMessage()
                flash(self.message, "danger")
                return redirect(backTo())
            session["compareIds"] = idpIds + [idpId]
        return redirect(backTo())

    def displayComparison(self):
        """2.2: the table of style, budget, location, property type, category and designer.
        It sets what the page shows and `render` draws it once, so a page that shows the
        table and then the 3a message is drawn a single time."""

    def displayMessage(self):
        """1.1, 2.3 and 2.4: `message`. After a tick `post` flashes it on the page the user
        was on. On the comparison page it is drawn with the table, if there is one."""

    def render(self):
        return render_template("compare/compare.html", idps=self.idps, message=self.message)


bp.add_url_rule("/compare", view_func=CompareIDPPage.as_view("compare"), methods=["GET"])
bp.add_url_rule(
    "/compare/select", view_func=CompareIDPPage.as_view("select"), methods=["POST"]
)
bp.add_url_rule("/compare/clear", view_func=CompareIDPPage.as_view("clear"), methods=["POST"])
