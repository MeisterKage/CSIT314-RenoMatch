from flask import Blueprint, redirect, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("designer", __name__, url_prefix="/designer")


class DesignerHomePage(MethodView):
    """Designers use the website home page, so this old address sends them there."""

    decorators = [role_required("designer")]

    def get(self):
        return redirect(url_for("public.home"))


bp.add_url_rule("/", view_func=DesignerHomePage.as_view("home"))
