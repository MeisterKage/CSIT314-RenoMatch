"""US-48 controller: the loop, alt and opt of the sequence diagram."""

import logging
from datetime import timedelta

from app.boundary.email_service import EmailService
from app.control.send_weekly_summary_controller import SendWeeklySummaryController
from app.entity import IDPEntity, PlatformActivityEntity, db
from app.entity.db import utcnow


class StubEmailService:
    """Records each send. `results` is the list of values to return, the last one repeating."""

    def __init__(self, results=(True,)):
        self.results = list(results)
        self.sent = []

    def sendSummaryEmail(self, email, content):
        self.sent.append((email, content))
        index = min(len(self.sent) - 1, len(self.results) - 1)
        return self.results[index]


def addViews(idp, count):
    for _ in range(count):
        db.session.add(
            PlatformActivityEntity(
                activityType="view", idpId=idp.idpId, timestamp=utcnow() - timedelta(days=1)
            )
        )
    db.session.commit()


def build(stub):
    controller = SendWeeklySummaryController()
    controller.emailService = stub
    return controller


def test_controller_holds_its_collaborators():
    controller = SendWeeklySummaryController()
    assert controller.entity is IDPEntity
    assert isinstance(controller.emailService, EmailService)


def test_sends_a_summary_to_each_opted_in_designer(make_account, make_idp):
    active = make_account(role="designer")
    quiet = make_account(role="designer")
    make_account(role="designer", weeklySummaryOptIn=False)
    addViews(make_idp(active, title="Sunny loft"), 3)
    stub = StubEmailService()

    build(stub).sendWeeklySummaries()

    emails = {email: content for email, content in stub.sent}
    assert set(emails) == {active.email, quiet.email}
    assert "3" in emails[active.email] and "Sunny loft" in emails[active.email]


def test_alt_summary_has_activity_composes_the_summary(make_account, make_idp, monkeypatch):
    designer = make_account(role="designer")
    addViews(make_idp(designer), 2)
    controller = build(StubEmailService())
    calls = []
    monkeypatch.setattr(
        controller, "composeSummary", lambda summary: calls.append("composeSummary") or "S"
    )
    monkeypatch.setattr(
        controller, "composeNoActivityNotice", lambda: calls.append("composeNoActivityNotice")
    )

    controller.sendWeeklySummaries()

    assert calls == ["composeSummary"]
    assert controller.emailService.sent == [(designer.email, "S")]


def test_alt_no_activity_composes_the_notice(make_account, make_idp, monkeypatch):
    designer = make_account(role="designer")
    make_idp(designer)
    controller = build(StubEmailService())
    calls = []
    monkeypatch.setattr(controller, "composeSummary", lambda summary: calls.append("summary"))
    monkeypatch.setattr(
        controller, "composeNoActivityNotice", lambda: calls.append("notice") or "N"
    )

    controller.sendWeeklySummaries()

    assert calls == ["notice"]
    assert controller.emailService.sent == [(designer.email, "N")]


def test_no_activity_notice_wording(make_account):
    make_account(role="designer")
    stub = StubEmailService()
    build(stub).sendWeeklySummaries()
    content = stub.sent[0][1]
    assert "No new activity this week" in content
    assert "portfolio" in content


def test_composeSummary_shows_totals_and_top_idps(make_account):
    from app.entity.reports import Summary

    designer = make_account(role="designer")
    summary = Summary(
        designerId=designer.userId,
        startDate=utcnow().date(),
        endDate=utcnow().date(),
        designerName="Dana",
        totalViews=9,
        totalShortlists=4,
        topIDPs=[("Alpha", 5), ("Bravo", 3)],
    )
    content = SendWeeklySummaryController().composeSummary(summary)
    assert "Dana" in content
    assert "Views: 9" in content
    assert "Shortlists: 4" in content
    assert content.index("Alpha") < content.index("Bravo")


def test_opt_not_taken_when_sent(make_account, monkeypatch):
    make_account(role="designer")
    controller = build(StubEmailService([True]))
    retries = []
    monkeypatch.setattr(controller, "scheduleRetry", lambda designerId: retries.append(designerId))
    controller.sendWeeklySummaries()
    assert retries == []


def test_opt_scheduleRetry_called_with_designerId_when_send_fails(make_account, monkeypatch):
    designer = make_account(role="designer")
    controller = build(StubEmailService([False]))
    retries = []
    monkeypatch.setattr(controller, "scheduleRetry", lambda designerId: retries.append(designerId))
    controller.sendWeeklySummaries()
    assert retries == [designer.userId]


def test_retry_succeeds_after_two_failures(make_account):
    make_account(role="designer")
    stub = StubEmailService([False, False, True])
    build(stub).sendWeeklySummaries()
    assert len(stub.sent) == 3
    assert len({content for _, content in stub.sent}) == 1


def test_retry_gives_up_after_three_retries(make_account, caplog):
    make_account(role="designer")
    stub = StubEmailService([False])
    with caplog.at_level(logging.WARNING):
        build(stub).sendWeeklySummaries()
    assert len(stub.sent) == 4  # the first send plus 3 retries
    assert "Giving up" in caplog.text


def test_a_failure_does_not_stop_the_loop(make_account):
    make_account(role="designer")
    second = make_account(role="designer")
    stub = StubEmailService([False, False, False, False, True])
    build(stub).sendWeeklySummaries()
    assert stub.sent[-1][0] == second.email


def test_call_order_follows_the_sequence_diagram(make_account, make_idp, monkeypatch):
    first = make_account(role="designer")
    second = make_account(role="designer")
    addViews(make_idp(first), 1)
    controller = build(StubEmailService([True, False, True]))
    order = []

    def spy(owner, name):
        original = getattr(owner, name)

        def wrapper(*args):
            order.append(name)
            return original(*args)

        monkeypatch.setattr(owner, name, wrapper)

    for name in ("getOptedInDesigners", "getWeeklyStats"):
        spy(IDPEntity, name)
    for name in ("composeSummary", "composeNoActivityNotice", "scheduleRetry"):
        spy(controller, name)
    original = controller.emailService.sendSummaryEmail

    def send(email, content):
        order.append("sendSummaryEmail")
        return original(email, content)

    monkeypatch.setattr(controller.emailService, "sendSummaryEmail", send)

    controller.sendWeeklySummaries()

    assert first.userId and second.userId
    assert order == [
        "getOptedInDesigners",
        "getWeeklyStats",
        "composeSummary",
        "sendSummaryEmail",
        "getWeeklyStats",
        "composeNoActivityNotice",
        "sendSummaryEmail",
        "scheduleRetry",
        "sendSummaryEmail",
    ]
