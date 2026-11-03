"""US-48 entity methods: who gets the weekly summary and what it says."""

from datetime import timedelta

from app.entity import IDPEntity, PlatformActivityEntity, db
from app.entity.db import utcnow
from app.entity.reports import Summary


def addActivity(idp, activityType, daysAgo, count=1):
    for _ in range(count):
        db.session.add(
            PlatformActivityEntity(
                activityType=activityType,
                idpId=idp.idpId,
                timestamp=utcnow() - timedelta(days=daysAgo),
            )
        )
    db.session.commit()


def test_getOptedInDesigners_returns_only_active_opted_in_designers(make_account):
    wanted = make_account(role="designer")
    optedOut = make_account(role="designer")
    optedOut.weeklySummaryOptIn = False
    suspended = make_account(role="designer")
    suspended.status = "Suspended"
    db.session.commit()
    make_account(role="customer")
    assert IDPEntity.getOptedInDesigners() == [wanted]


def test_getWeeklyStats_counts_the_last_seven_days_only(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer)
    other = make_idp()
    addActivity(idp, "view", 1, count=3)
    addActivity(idp, "view", 9, count=5)
    addActivity(idp, "shortlist", 2, count=2)
    addActivity(idp, "shortlist", 30)
    addActivity(other, "view", 1, count=4)

    summary = IDPEntity.getWeeklyStats(designer.userId)

    assert isinstance(summary, Summary)
    assert summary.designerId == designer.userId
    assert summary.designerName == designer.name
    assert summary.totalViews == 3
    assert summary.totalShortlists == 2
    assert summary.hasActivity


def test_getWeeklyStats_lists_the_top_three_idps_by_views(make_account, make_idp):
    designer = make_account(role="designer")
    for title, views in (("Alpha", 1), ("Bravo", 4), ("Charlie", 2), ("Delta", 3), ("Echo", 0)):
        addActivity(make_idp(designer, title=title), "view", 1, count=views)

    summary = IDPEntity.getWeeklyStats(designer.userId)

    assert summary.topIDPs == [("Bravo", 4), ("Delta", 3), ("Charlie", 2)]


def test_getWeeklyStats_with_no_activity(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer)
    addActivity(idp, "view", 20)
    summary = IDPEntity.getWeeklyStats(designer.userId)
    assert (summary.totalViews, summary.totalShortlists, summary.topIDPs) == (0, 0, [])
    assert not summary.hasActivity
