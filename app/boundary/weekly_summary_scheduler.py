import hmac
import os

import click
from flask import Blueprint, abort, request
from flask.views import MethodView

from app import csrf
from app.control.send_weekly_summary_controller import SendWeeklySummaryController

bp = Blueprint("weekly_summary", __name__)

TOKEN_HEADER = "X-Summary-Token"


class WeeklySummaryScheduler(MethodView):
    """Boundary for US-48. The System Scheduler calls `triggerWeeklySummary()` (step 1) through
    the CLI command `flask --app app send-weekly-summaries` or `POST /internal/weekly-summary`,
    which a scheduled GitHub Actions workflow calls every Monday at 01:00 UTC."""

    def __init__(self):
        self.controller = SendWeeklySummaryController()

    def post(self):
        expected = os.environ.get("WEEKLY_SUMMARY_TOKEN")
        if not expected:
            abort(404)  # no token configured: the endpoint is disabled
        if not hmac.compare_digest(request.headers.get(TOKEN_HEADER, ""), expected):
            abort(403)
        self.triggerWeeklySummary()
        return {"status": "sent"}

    def triggerWeeklySummary(self) -> None:
        self.controller.sendWeeklySummaries()  # 1.1


view = csrf.exempt(WeeklySummaryScheduler.as_view("weekly_summary"))  # the token replaces CSRF
bp.add_url_rule("/internal/weekly-summary", view_func=view, methods=["POST"])


def register_weekly_summary_command(app) -> None:
    @app.cli.command("send-weekly-summaries")
    def sendWeeklySummariesCommand():
        """Email the weekly summary to every opted-in designer."""
        WeeklySummaryScheduler().triggerWeeklySummary()
        click.echo("Weekly summaries sent.")
