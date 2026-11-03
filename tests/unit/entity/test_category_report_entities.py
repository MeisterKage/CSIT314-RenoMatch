from datetime import date, datetime

import pytest

from app.entity import CategoryEntity, PlatformActivityEntity, db
from app.entity.reports import Report


def addActivity(activityType, when, userId=None, idpId=None):
    db.session.add(
        PlatformActivityEntity(
            activityType=activityType, userId=userId, idpId=idpId, timestamp=when
        )
    )
    db.session.commit()


# Categories (US-49 to US-54)


def test_create_category_defaults_to_active(app):
    category = CategoryEntity.createCategory("Scandinavian", "Light and simple")
    assert category.status == "Active"
    assert CategoryEntity.findById(category.categoryId).name == "Scandinavian"


def test_name_taken_ignores_case_and_can_exclude_one_category(app):
    category = CategoryEntity.createCategory("Minimalist", "")
    assert CategoryEntity.nameTaken("  minimalIST ")
    assert not CategoryEntity.nameTaken("Industrial")
    assert not CategoryEntity.nameTaken("minimalist", category.categoryId)


def test_update_suspend_and_reactivate(app):
    category = CategoryEntity.createCategory("Rustic", "Old")
    category.updateCategory("Rustic Style", "New")
    assert (category.name, category.description) == ("Rustic Style", "New")
    category.suspend()
    assert category.status == "Suspended"
    assert category not in CategoryEntity.getActiveCategories()
    category.reactivate()
    assert category.status == "Active"
    assert category in CategoryEntity.getActiveCategories()


@pytest.fixture
def searchable(app):
    CategoryEntity.createCategory("Modern Living", "")
    CategoryEntity.createCategory("100% Wood", "")
    CategoryEntity.createCategory("Under_score", "")
    CategoryEntity.createCategory("Classic", "").suspend()


def names(categories):
    return [category.name for category in categories]


def test_search_is_case_insensitive_name_contains(searchable):
    assert names(CategoryEntity.searchCategories("LIVING", "")) == ["Modern Living"]
    assert names(CategoryEntity.searchCategories("ern", "")) == ["Modern Living"]


def test_search_escapes_percent_and_underscore(searchable):
    assert names(CategoryEntity.searchCategories("%", "")) == ["100% Wood"]
    assert names(CategoryEntity.searchCategories("_", "")) == ["Under_score"]


def test_search_status_filter_and_all(searchable):
    assert names(CategoryEntity.searchCategories("", "Suspended")) == ["Classic"]
    assert "Classic" not in names(CategoryEntity.searchCategories("", "Active"))
    assert names(CategoryEntity.searchCategories("", "")) == [
        "100% Wood",
        "Classic",
        "Modern Living",
        "Under_score",
    ]
    assert names(CategoryEntity.searchCategories("", "all")) == names(
        CategoryEntity.searchCategories("", "")
    )


def test_search_returns_nothing_when_no_name_matches(searchable):
    assert CategoryEntity.searchCategories("zzz", "") == []


def test_search_results_carry_idp_count(app, make_idp, make_category):
    category = make_category(name="Counted")
    make_idp(category=category)
    make_idp(category=category, status="Removed")
    assert CategoryEntity.searchCategories("counted", "")[0].idpCount == 1


# Reports (US-55, US-56, US-59)


@pytest.fixture
def activity(make_account):
    """October 2026 and September 2026 activity with known counts."""
    designer = make_account(role="designer")
    customer = make_account(role="customer")
    other = make_account(role="customer")
    for when in (datetime(2026, 10, 1, 0, 0), datetime(2026, 10, 31, 23, 59)):
        addActivity("register", when, customer.userId)
    addActivity("register", datetime(2026, 10, 15, 9), designer.userId)
    addActivity("register", datetime(2026, 9, 30, 23, 59), other.userId)
    for _ in range(2):
        addActivity("idp_added", datetime(2026, 10, 5, 9), designer.userId)
    addActivity("idp_added", datetime(2026, 9, 5, 9), designer.userId)
    for _ in range(5):
        addActivity("view", datetime(2026, 10, 10, 12), customer.userId)
    for _ in range(3):
        addActivity("view", datetime(2026, 9, 10, 12), customer.userId)
    addActivity("view", datetime(2026, 11, 1, 0, 0), customer.userId)
    for _ in range(2):
        addActivity("shortlist", datetime(2026, 10, 11, 8), customer.userId)
    for _ in range(4):
        addActivity("shortlist", datetime(2026, 9, 11, 8), customer.userId)
    addActivity("enquiry", datetime(2026, 10, 12, 8), customer.userId)
    addActivity("review", datetime(2026, 10, 12, 8), customer.userId)


def test_generate_monthly_report_counts_and_compares(activity):
    report = PlatformActivityEntity.generateMonthlyReport(10, 2026)
    assert isinstance(report, Report)
    assert report.reportType == "monthly"
    assert (report.startDate, report.endDate) == (date(2026, 10, 1), date(2026, 10, 31))
    assert report.newUsers == 3
    assert report.newDesigners == 1
    assert report.newIDPs == 2
    assert report.idpViews == 5
    assert report.shortlists == 2
    assert report.enquiries == 1
    previous = report.previous
    assert (previous.startDate, previous.endDate) == (date(2026, 9, 1), date(2026, 9, 30))
    assert (previous.newUsers, previous.newDesigners, previous.newIDPs) == (1, 0, 1)
    assert (previous.idpViews, previous.shortlists, previous.enquiries) == (3, 4, 0)
    assert report.change("newUsers") == 2
    assert report.change("shortlists") == -2
    assert report.hasActivity


def test_monthly_report_in_january_compares_with_december(activity):
    report = PlatformActivityEntity.generateMonthlyReport(1, 2027)
    assert report.previous.startDate == date(2026, 12, 1)
    assert report.previous.endDate == date(2026, 12, 31)
    assert not report.hasActivity


def test_month_with_no_activity_is_all_zeros(app):
    report = PlatformActivityEntity.generateMonthlyReport(3, 2026)
    assert not report.hasActivity
    assert [report.newUsers, report.idpViews, report.enquiries] == [0, 0, 0]


def test_generate_report_range_and_equal_length_previous_period(activity):
    report = PlatformActivityEntity.generateReport(date(2026, 10, 10), date(2026, 10, 12))
    assert report.idpViews == 5
    assert report.previous.startDate == date(2026, 10, 7)
    assert report.previous.endDate == date(2026, 10, 9)
    assert report.previous.idpViews == 0


def test_single_day_report_compares_with_the_day_before(activity):
    report = PlatformActivityEntity.generateReport(date(2026, 10, 1), date(2026, 10, 1))
    assert report.newUsers == 1
    assert report.previous.startDate == report.previous.endDate == date(2026, 9, 30)
    assert report.previous.newUsers == 1
    assert report.change("newUsers") == 0
