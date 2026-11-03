from datetime import date, datetime, timedelta

import pytest

from app.control.create_category_controller import CreateCategoryController
from app.control.errors import ValidationError
from app.control.export_report_pdf_controller import ExportReportPDFController
from app.control.generate_custom_report_controller import GenerateCustomReportController
from app.control.generate_daily_report_controller import GenerateDailyReportController
from app.control.generate_monthly_report_controller import GenerateMonthlyReportController
from app.control.reactivate_category_controller import ReactivateCategoryController
from app.control.search_categories_controller import SearchCategoriesController
from app.control.suspend_category_controller import SuspendCategoryController
from app.control.update_category_controller import UpdateCategoryController
from app.control.view_category_controller import ViewCategoryController
from app.entity import CategoryEntity, PlatformActivityEntity, db
from app.entity.db import utcnow

# Categories


def test_create_category_validates_and_enforces_unique_names(app):
    category = CreateCategoryController().createCategory("  Bohemian ", " Free spirited ")
    assert (category.name, category.description) == ("Bohemian", "Free spirited")
    for name, description, field in (
        ("bohemian", "", "name"),
        ("   ", "", "name"),
        ("x" * 61, "", "name"),
        ("Fine", "d" * 256, "description"),
    ):
        with pytest.raises(ValidationError) as exc:
            CreateCategoryController().createCategory(name, description)
        assert field in exc.value.errors


def test_get_category_returns_it_or_none(app, make_category):
    category = make_category(name="Viewable")
    assert ViewCategoryController().getCategory(category.categoryId).idpCount == 0
    assert ViewCategoryController().getCategory(9999) is None


def test_update_category_allows_keeping_own_name_but_not_another(app, make_category):
    one, two = make_category(name="One"), make_category(name="Two")
    UpdateCategoryController().updateCategory(one.categoryId, "ONE", "changed")
    assert (one.name, one.description) == ("ONE", "changed")
    with pytest.raises(ValidationError) as exc:
        UpdateCategoryController().updateCategory(two.categoryId, "one", "")
    assert "name" in exc.value.errors
    with pytest.raises(ValidationError):
        UpdateCategoryController().updateCategory(9999, "Whatever", "")


def test_suspend_and_reactivate_category(app, make_category):
    category = make_category(name="Toggle")
    assert SuspendCategoryController().suspendCategory(category.categoryId)
    assert category.status == "Suspended"
    with pytest.raises(ValidationError):
        SuspendCategoryController().suspendCategory(category.categoryId)
    assert ReactivateCategoryController().reactivateCategory(category.categoryId)
    assert category.status == "Active"
    with pytest.raises(ValidationError):
        ReactivateCategoryController().reactivateCategory(category.categoryId)
    with pytest.raises(ValidationError):
        SuspendCategoryController().suspendCategory(9999)


def test_search_controller_holds_entity_and_delegates(app, monkeypatch):
    controller = SearchCategoriesController()
    assert controller.entity is CategoryEntity
    calls = []
    monkeypatch.setattr(
        CategoryEntity,
        "searchCategories",
        lambda keyword, status: calls.append((keyword, status)) or [],
    )
    assert controller.searchCategories("wood", "Active") == []
    assert calls == [("wood", "Active")]


# Reports


def firstOfNextMonth():
    today = utcnow().date()
    return (today.replace(day=1) + timedelta(days=32)).replace(day=1)


def test_monthly_controller_holds_entity(app):
    assert GenerateMonthlyReportController().entity is PlatformActivityEntity


def test_future_month_returns_none_without_calling_the_entity(app, monkeypatch):
    called = []
    monkeypatch.setattr(
        PlatformActivityEntity, "generateMonthlyReport", lambda month, year: called.append(1)
    )
    future = firstOfNextMonth()
    controller = GenerateMonthlyReportController()
    assert controller.generateMonthlyReport(future.month, future.year) is None
    assert controller.generateMonthlyReport(1, utcnow().year + 1) is None
    assert called == []


def test_current_and_past_months_call_the_entity_once_each(app, monkeypatch):
    calls = []
    sentinel = object()
    monkeypatch.setattr(
        PlatformActivityEntity,
        "generateMonthlyReport",
        lambda month, year: calls.append((month, year)) or sentinel,
    )
    today = utcnow().date()
    controller = GenerateMonthlyReportController()
    assert controller.generateMonthlyReport(today.month, today.year) is sentinel
    assert controller.generateMonthlyReport(1, 2020) is sentinel
    assert calls == [(today.month, today.year), (1, 2020)]


def test_monthly_controller_returns_the_empty_report(app):
    report = GenerateMonthlyReportController().generateMonthlyReport(1, 2020)
    assert not report.hasActivity


def seedDays(make_account):
    customer = make_account(role="customer")
    for day, count in ((date(2026, 10, 9), 2), (date(2026, 10, 10), 5)):
        for _ in range(count):
            db.session.add(
                PlatformActivityEntity(
                    activityType="view",
                    userId=customer.userId,
                    timestamp=datetime(day.year, day.month, day.day, 12),
                )
            )
    db.session.commit()


def test_daily_report_compares_with_the_previous_day(app, make_account):
    seedDays(make_account)
    report = GenerateDailyReportController().generateDailyReport(date(2026, 10, 10))
    assert report.reportType == "daily"
    assert report.idpViews == 5
    assert report.previous.idpViews == 2
    assert report.change("idpViews") == 3
    assert GenerateDailyReportController().entity is PlatformActivityEntity


def test_custom_report_compares_with_equal_length_period(app, make_account):
    seedDays(make_account)
    report = GenerateCustomReportController().generateCustomReport(
        date(2026, 10, 10), date(2026, 10, 11)
    )
    assert report.reportType == "custom"
    assert report.idpViews == 5
    assert report.previous.idpViews == 2
    assert (report.previous.startDate, report.previous.endDate) == (
        date(2026, 10, 8),
        date(2026, 10, 9),
    )


def test_custom_report_rejects_start_after_end(app):
    controller = GenerateCustomReportController()
    assert controller.generateCustomReport(date(2026, 10, 11), date(2026, 10, 10)) is None


def test_custom_report_allows_a_single_day(app):
    controller = GenerateCustomReportController()
    assert controller.generateCustomReport(date(2026, 10, 10), date(2026, 10, 10)) is not None


def test_pdf_export_is_a_pdf_for_each_report_type(app, make_account):
    seedDays(make_account)
    controller = ExportReportPDFController()
    daily = controller.exportReportPDF("daily", {"date": "2026-10-10"})
    monthly = controller.exportReportPDF("monthly", {"month": "10", "year": "2026"})
    custom = controller.exportReportPDF(
        "custom", {"startDate": "2026-10-01", "endDate": "2026-10-31"}
    )
    for pdf in (daily, monthly, custom):
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")


def test_pdf_export_refuses_bad_parameters(app):
    controller = ExportReportPDFController()
    future = firstOfNextMonth()
    futureParams = {"month": str(future.month), "year": str(future.year)}
    assert controller.exportReportPDF("monthly", futureParams) is None
    assert controller.exportReportPDF("monthly", {"month": "13", "year": "2026"}) is None
    assert controller.exportReportPDF("daily", {"date": "nope"}) is None
    badRange = {"startDate": "2026-10-11", "endDate": "2026-10-10"}
    assert controller.exportReportPDF("custom", badRange) is None
    assert controller.exportReportPDF("weekly", {}) is None
