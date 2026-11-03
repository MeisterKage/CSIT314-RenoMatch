from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask.views import MethodView

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
    return path if path.startswith("/") else url_for("compare.compare")


def selectedIds() -> list[int]:
    return list(session.get("compareIds", []))


@bp.app_context_processor
def injectCompareCount():
    return {"compareCount": len(selectedIds())}


class CompareIDPPage(MethodView):
    """Boundary for US-13. The selection of up to 3 IDP ids is kept in the session.

    `post` on /compare/select is sequence step 1 (tick "Compare" on an IDP), with
    1.1 displayMessage() when 3 are already selected (opt 1a). `get` on /compare is step 2
    (click "Compare"): 2.1 compareIDPs, then 2.2 displayComparison, or 2.3 displayMessage
    (alt 2a), and 2.4 displayMessage when a selected IDP is no longer available (opt 3a).
    Both display methods take no argument, as in the class diagram, so the data they show
    is held in `idps` and `message`.
    """

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
            return self.displayMessage()
        if len(self.idps) < len(idpIds):
            session["compareIds"] = [idp.idpId for idp in self.idps]
            self.displayComparison()
            self.message = UNAVAILABLE
            return self.displayMessage()
        return self.displayComparison()

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
                return self.displayMessage()
            session["compareIds"] = idpIds + [idpId]
        return redirect(backTo())

    def displayComparison(self):
        """2.2: the table of style, budget, location, property type, category and designer."""
        return render_template("compare/compare.html", idps=self.idps, message=self.message)

    def displayMessage(self):
        """1.1, 2.3 and 2.4: `message`. After a tick it is flashed on the page the user was on."""
        if request.method == "POST":
            flash(self.message, "danger")
            return redirect(backTo())
        return render_template("compare/compare.html", idps=self.idps, message=self.message)


bp.add_url_rule("/compare", view_func=CompareIDPPage.as_view("compare"), methods=["GET"])
bp.add_url_rule(
    "/compare/select", view_func=CompareIDPPage.as_view("select"), methods=["POST"]
)
bp.add_url_rule("/compare/clear", view_func=CompareIDPPage.as_view("clear"), methods=["POST"])
