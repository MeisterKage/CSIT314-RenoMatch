from flask import Blueprint, jsonify, render_template
from flask.views import MethodView

bp = Blueprint("public", __name__)


class HomePage(MethodView):
    def get(self):
        return render_template("public/home.html")


class HealthCheck(MethodView):
    def get(self):
        return jsonify(status="ok")


bp.add_url_rule("/", view_func=HomePage.as_view("home"))
bp.add_url_rule("/health", view_func=HealthCheck.as_view("health"))
