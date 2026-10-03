from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("designer", __name__, url_prefix="/designer")


class DesignerHomePage(MethodView):
    decorators = [role_required("designer")]

    def get(self):
        return render_template("role_home.html", role_label="Interior Designer")


bp.add_url_rule("/", view_func=DesignerHomePage.as_view("home"))
