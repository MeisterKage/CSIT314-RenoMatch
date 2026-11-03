"""US-48 boundary: WeeklySummaryScheduler, the internal endpoint, the CLI and the workflow."""

import logging
from pathlib import Path

from app.boundary.weekly_summary_scheduler import WeeklySummaryScheduler
from app.control.send_weekly_summary_controller import SendWeeklySummaryController

ENDPOINT = "/internal/weekly-summary"
TOKEN = "s3cret-token"


def test_scheduler_holds_the_controller(app):
    assert isinstance(WeeklySummaryScheduler().controller, SendWeeklySummaryController)


def test_triggerWeeklySummary_calls_sendWeeklySummaries(app):
    scheduler = WeeklySummaryScheduler()
    calls = []
    scheduler.controller.sendWeeklySummaries = lambda: calls.append("sendWeeklySummaries")
    scheduler.triggerWeeklySummary()
    assert calls == ["sendWeeklySummaries"]


def test_endpoint_is_disabled_without_a_configured_token(client, monkeypatch):
    monkeypatch.delenv("WEEKLY_SUMMARY_TOKEN", raising=False)
    response = client.post(ENDPOINT, headers={"X-Summary-Token": "anything"})
    assert response.status_code == 404


def test_endpoint_rejects_a_missing_or_wrong_token(client, make_account, monkeypatch, caplog):
    monkeypatch.setenv("WEEKLY_SUMMARY_TOKEN", TOKEN)
    make_account(role="designer")
    with caplog.at_level(logging.INFO):
        assert client.post(ENDPOINT).status_code == 403
        assert client.post(ENDPOINT, headers={"X-Summary-Token": "nope"}).status_code == 403
    assert "Email to" not in caplog.text


def test_endpoint_with_the_token_sends_the_emails(client, make_account, monkeypatch, caplog):
    monkeypatch.setenv("WEEKLY_SUMMARY_TOKEN", TOKEN)
    designer = make_account(role="designer")
    with caplog.at_level(logging.INFO):
        response = client.post(ENDPOINT, headers={"X-Summary-Token": TOKEN})
    assert response.status_code == 200
    assert f"Email to {designer.email}" in caplog.text
    assert "Your RenoMatch weekly summary" in caplog.text
    assert "No new activity this week" in caplog.text


def test_endpoint_is_exempt_from_csrf(app, client, monkeypatch):
    monkeypatch.setenv("WEEKLY_SUMMARY_TOKEN", TOKEN)
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post(ENDPOINT, headers={"X-Summary-Token": TOKEN})
    assert response.status_code == 200


def test_endpoint_only_accepts_post(client, monkeypatch):
    monkeypatch.setenv("WEEKLY_SUMMARY_TOKEN", TOKEN)
    assert client.get(ENDPOINT, headers={"X-Summary-Token": TOKEN}).status_code == 405


def test_cli_command_sends_the_summaries(app, make_account, caplog):
    designer = make_account(role="designer")
    with caplog.at_level(logging.INFO):
        result = app.test_cli_runner().invoke(args=["send-weekly-summaries"])
    assert result.exit_code == 0
    assert "Weekly summaries sent." in result.output
    assert f"Email to {designer.email}" in caplog.text


def test_github_workflow_schedule():
    text = (Path(__file__).resolve().parents[2] / ".github/workflows/weekly-summary.yml").read_text()
    assert 'cron: "0 1 * * 1"' in text
    assert "workflow_dispatch" in text
    assert "/internal/weekly-summary" in text
    assert "X-Summary-Token" in text
    assert "secrets.RENDER_APP_URL" in text
    assert "secrets.WEEKLY_SUMMARY_TOKEN" in text
    assert "exit 0" in text
