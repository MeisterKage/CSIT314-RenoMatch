"""The entity model of spec section 3: status strings, counters, photoUrls and activity."""

from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import (
    AuditLogEntity,
    IDPEntity,
    IDPFlagEntity,
    PlatformActivityEntity,
    ReviewEntity,
    UserProfileEntity,
    db,
)
from app.entity.db import utcnow
from app.entity.platform_activity import ACTIVITY_TYPES
from app.entity.reports import Report, Summary


def reload(entity_class, key):
    db.session.expire_all()
    return db.session.get(entity_class, key)


# Status strings


def test_new_account_is_active_and_opted_in_to_the_weekly_summary(make_account):
    account = make_account()
    assert account.status == "Active"
    assert account.weeklySummaryOptIn is True
    assert account.resetToken is None
    assert account.tokenExpiry is None


def test_suspended_account_status_blocks_login(make_account):
    account = make_account()
    account.status = "Suspended"
    assert not account.canLogIn()


def test_new_profile_is_active(app):
    profile = UserProfileEntity.createUserProfile("Customer", "customer")
    assert profile.status == "Active"
    assert profile.roleType == "customer"


def test_suspended_profile_status_blocks_login(make_account):
    account = make_account()
    account.profile.status = "Suspended"
    assert not account.canLogIn()


def test_new_category_is_active(make_category):
    assert make_category().status == "Active"


def test_new_idp_is_active_current_and_unfeatured(make_idp):
    idp = make_idp()
    assert idp.status == "Active"
    assert idp.stage == "Current"
    assert idp.isFeatured is False
    assert idp.featuredDate is None


def test_new_flag_is_open_and_unreviewed(make_account, make_idp):
    idp, reporter = make_idp(), make_account()
    flag = IDPFlagEntity(idpId=idp.idpId, reporterId=reporter.userId, reason="Copied photos")
    db.session.add(flag)
    db.session.commit()
    assert flag.status == "Open"
    assert flag.reviewedBy is None
    assert flag.createdAt is not None


# CategoryEntity.idpCount


def test_idp_count_counts_only_active_idps_in_the_category(make_category, make_idp):
    category, other = make_category(), make_category()
    make_idp(category=category)
    make_idp(category=category)
    make_idp(category=category, status="Suspended")
    make_idp(category=category, status="Removed")
    make_idp(category=other)
    assert category.idpCount == 2
    assert other.idpCount == 1


def test_idp_count_is_zero_for_an_empty_category(make_category):
    assert make_category().idpCount == 0


# IDPEntity counters, photoUrls and featuring


def test_new_idp_counters_start_at_zero(make_idp):
    idp = make_idp()
    assert (idp.viewCount, idp.shortlistCount) == (0, 0)


def test_idp_counters_are_stored(make_idp):
    idp = make_idp()
    idp.viewCount += 3
    idp.shortlistCount += 1
    db.session.commit()
    reloaded = reload(IDPEntity, idp.idpId)
    assert (reloaded.viewCount, reloaded.shortlistCount) == (3, 1)


def test_new_idp_has_no_photo_urls(make_idp):
    assert make_idp().photoUrls == []


def test_photo_urls_are_stored_as_an_ordered_list(make_idp):
    urls = ["/static/img/idp/idp-07.jpg", "/static/img/idp/idp-01.jpg"]
    idp = make_idp(photoUrls=urls)
    assert reload(IDPEntity, idp.idpId).photoUrls == urls


def test_idp_budget_is_a_float(make_idp):
    idp = make_idp(budget=45250.5)
    assert reload(IDPEntity, idp.idpId).budget == 45250.5


def test_featured_idp_keeps_its_featured_date(make_idp):
    idp = make_idp(isFeatured=True, featuredDate=date(2026, 11, 1))
    reloaded = reload(IDPEntity, idp.idpId)
    assert reloaded.isFeatured is True
    assert reloaded.featuredDate == date(2026, 11, 1)


# PlatformActivityEntity


def test_activity_types_are_the_spec_values():
    assert ACTIVITY_TYPES == ("view", "shortlist", "register", "enquiry", "review", "idp_added")


def test_platform_activity_records_type_user_idp_and_timestamp(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    activity = PlatformActivityEntity(
        activityType="shortlist", userId=customer.userId, idpId=idp.idpId
    )
    db.session.add(activity)
    db.session.commit()
    reloaded = reload(PlatformActivityEntity, activity.activityId)
    assert (reloaded.activityType, reloaded.userId, reloaded.idpId) == (
        "shortlist",
        customer.userId,
        idp.idpId,
    )
    assert utcnow() - reloaded.timestamp < timedelta(minutes=1)


def test_platform_activity_allows_anonymous_view_and_register_without_idp(
    make_account, make_idp
):
    db.session.add_all(
        [
            PlatformActivityEntity(activityType="view", userId=None, idpId=make_idp().idpId),
            PlatformActivityEntity(
                activityType="register", userId=make_account().userId, idpId=None
            ),
        ]
    )
    db.session.commit()
    assert db.session.query(PlatformActivityEntity).count() == 2


# ReviewEntity and AuditLogEntity rules


def test_one_review_per_designer_and_user(make_account):
    customer, designer = make_account(), make_account(role="designer")
    pair = {"designerId": designer.userId, "userId": customer.userId}
    db.session.add(ReviewEntity(rating=5, **pair))
    db.session.commit()
    db.session.add(ReviewEntity(rating=3, **pair))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_audit_log_is_read_only_after_insert(make_account):
    admin, target = make_account(role="admin"), make_account()
    entry = AuditLogEntity(
        adminId=admin.userId,
        action="suspend_account",
        targetType="user_account",
        targetId=target.userId,
    )
    db.session.add(entry)
    db.session.commit()
    assert entry.timestamp is not None
    entry.action = "reactivate_account"
    with pytest.raises(ValueError, match="read-only"):
        db.session.commit()


# Report and Summary dataclasses


def test_report_compares_with_the_previous_period():
    previous = Report("monthly", date(2026, 9, 1), date(2026, 9, 30), newUsers=4, idpViews=10)
    report = Report(
        "monthly", date(2026, 10, 1), date(2026, 10, 31), newUsers=6, idpViews=7,
        previous=previous,
    )
    assert report.hasActivity
    assert report.change("newUsers") == 2
    assert report.change("idpViews") == -3
    assert report.change("enquiries") == 0


def test_empty_report_has_no_activity():
    report = Report("daily", date(2026, 10, 1), date(2026, 10, 1))
    assert not report.hasActivity
    assert report.change("newIDPs") == 0


def test_summary_has_activity_only_with_views_or_shortlists():
    week = (date(2026, 10, 26), date(2026, 11, 1))
    assert not Summary(7, *week).hasActivity
    busy = Summary(7, *week, totalViews=12, topIDPs=[("Modern HDB", 9), ("Loft", 3)])
    assert busy.hasActivity
    assert busy.topIDPs[0] == ("Modern HDB", 9)
