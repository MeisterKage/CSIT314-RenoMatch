from datetime import datetime, timedelta

import pytest

from app.boundary.categories import ManageCategoriesPage
from app.boundary.reports import ReportsPage
from app.control.generate_monthly_report_controller import GenerateMonthlyReportController
from app.control.search_categories_controller import SearchCategoriesController
from app.entity import CategoryEntity, PlatformActivityEntity, UserAccountEntity, db
from app.entity.db import utcnow


@pytest.fixture
def manager(make_account, login):
    account = make_account(role="platform", username="manager")
    login("manager")
    return account


def text(resp):
    return resp.get_data(as_text=True)


# Access


@pytest.mark.parametrize(
    "path",
    [
        "/platform/categories",
        "/platform/categories/new",
        "/platform/reports",
        "/platform/reports/pdf?type=daily&date=2026-10-10",
    ],
)
def test_pages_need_a_platform_manager(client, make_account, login, path):
    assert client.get(path).status_code == 302
    make_account(role="customer", username="cust")
    login("cust")
    assert client.get(path).status_code == 403


def test_boundaries_hold_the_diagram_controllers(app):
    assert isinstance(ManageCategoriesPage().controller, SearchCategoriesController)
    assert isinstance(ReportsPage().controller, GenerateMonthlyReportController)


# Categories


def test_list_shows_name_status_and_idp_count(client, manager, make_category, make_idp):
    category = make_category(name="Scandi")
    make_idp(category=category)
    make_category(name="Old", status="Suspended")
    page = text(client.get("/platform/categories"))
    assert "Scandi" in page and "Old" in page
    assert "Suspended" in page and "Active" in page
    assert "<td>1</td>" in page


def test_search_by_keyword_and_status(client, manager, make_category):
    make_category(name="Modern Living")
    make_category(name="Classic", status="Suspended")
    page = text(client.get("/platform/categories?keyword=LIVING"))
    assert "Modern Living" in page and "Classic" not in page
    page = text(client.get("/platform/categories?status=Suspended"))
    assert "Classic" in page and "Modern Living" not in page


def test_search_with_no_match_shows_the_message(client, manager, make_category):
    make_category(name="Modern")
    page = text(client.get("/platform/categories?keyword=zzz"))
    assert "No categories match your search" in page
    assert "<table" not in page


def test_create_category(client, manager):
    assert client.get("/platform/categories/new").status_code == 200
    resp = client.post("/platform/categories/new", data={"name": "Tropical", "description": "Lush"})
    category = CategoryEntity.query.filter_by(name="Tropical").one()
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/platform/categories/{category.categoryId}")


def test_create_category_rejects_duplicate_name_ignoring_case(client, manager, make_category):
    make_category(name="Tropical")
    resp = client.post("/platform/categories/new", data={"name": "tropical", "description": ""})
    assert resp.status_code == 200
    assert "already exists" in text(resp)
    assert CategoryEntity.query.count() == 1


def test_view_category_shows_idp_count(client, manager, make_category, make_idp):
    category = make_category(name="Viewed", description="About it")
    make_idp(category=category)
    make_idp(category=category)
    page = text(client.get(f"/platform/categories/{category.categoryId}"))
    assert "Viewed" in page and "About it" in page
    assert "<dd>2</dd>" in page


def test_unknown_category_is_404(client, manager):
    assert client.get("/platform/categories/9999").status_code == 404
    assert client.get("/platform/categories/9999/edit").status_code == 404


def test_update_category(client, manager, make_category):
    category = make_category(name="Before")
    assert client.get(f"/platform/categories/{category.categoryId}/edit").status_code == 200
    resp = client.post(
        f"/platform/categories/{category.categoryId}/edit",
        data={"name": "After", "description": "Changed"},
    )
    assert resp.status_code == 302
    assert db.session.get(CategoryEntity, category.categoryId).name == "After"


def test_update_category_rejects_another_categorys_name(client, manager, make_category):
    make_category(name="Taken")
    category = make_category(name="Mine")
    resp = client.post(
        f"/platform/categories/{category.categoryId}/edit", data={"name": "TAKEN", "description": ""}
    )
    assert resp.status_code == 200 and "already exists" in text(resp)


def test_suspend_and_reactivate_category(client, manager, make_category):
    category = make_category(name="Toggle")
    client.post(f"/platform/categories/{category.categoryId}/suspend")
    assert db.session.get(CategoryEntity, category.categoryId).status == "Suspended"
    client.post(f"/platform/categories/{category.categoryId}/reactivate")
    assert db.session.get(CategoryEntity, category.categoryId).status == "Active"


def test_suspended_category_is_hidden_from_browse_filter_and_add_idp(
    client, make_account, login, make_category
):
    make_category(name="Visible One")
    make_category(name="Hidden One", status="Suspended")
    assert "Hidden One" not in text(client.get("/idps"))
    assert "Visible One" in text(client.get("/idps"))
    designer = make_account(role="designer", username="designer")
    login(designer.username)
    page = text(client.get("/designer/portfolio/new"))
    assert "Visible One" in page and "Hidden One" not in page


# Navigation


def test_platform_nav_and_home_link_categories_and_reports(client, manager):
    for path in ("/platform/", "/platform/categories"):
        page = text(client.get(path))
        assert 'href="/platform/categories"' in page
        assert 'href="/platform/reports"' in page


# Registration activity feeds the report


def test_registering_records_a_register_activity(client):
    from app.entity import UserProfileEntity
    from app.entity.user_profile import DEFAULT_PROFILE_NAMES

    for role, name in DEFAULT_PROFILE_NAMES.items():
        UserProfileEntity.createUserProfile(name, role)
    client.post(
        "/register",
        data={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "Passw0rd!",
            "confirm_password": "Passw0rd!",
            "full_name": "New Bie",
            "phone": "",
            "role": "designer",
        },
    )
    account = UserAccountEntity.findByUsername("newbie")
    rows = PlatformActivityEntity.query.filter_by(activityType="register").all()
    assert [row.userId for row in rows] == [account.userId]


# Reports


def addActivity(activityType, when, userId=None):
    db.session.add(PlatformActivityEntity(activityType=activityType, userId=userId, timestamp=when))
    db.session.commit()


@pytest.fixture
def october(make_account):
    customer = make_account(role="customer")
    for _ in range(5):
        addActivity("view", datetime(2026, 10, 10, 12), customer.userId)
    for _ in range(3):
        addActivity("view", datetime(2026, 9, 10, 12), customer.userId)
    addActivity("enquiry", datetime(2026, 10, 12, 8), customer.userId)


def test_reports_page_links_the_three_report_types(client, manager):
    page = text(client.get("/platform/reports"))
    for kind in ("daily", "monthly", "custom"):
        assert f"/platform/reports?type={kind}" in page


def test_monthly_report_shows_figures_and_change(client, manager, october):
    page = text(client.get("/platform/reports?type=monthly&month=10&year=2026"))
    assert "IDP views" in page and "New registered users" in page
    assert "<td>5</td>" in page and "<td>3</td>" in page
    assert "+2" in page
    assert "no activity" not in page.lower()
    assert "/platform/reports/pdf?type=monthly&amp;month=10&amp;year=2026" in page


def test_monthly_report_for_a_future_month_shows_the_message(client, manager):
    future = (utcnow().date().replace(day=1) + timedelta(days=32)).replace(day=1)
    page = text(client.get(f"/platform/reports?type=monthly&month={future.month}&year={future.year}"))
    assert "Please select a past or current month" in page
    assert "IDP views" not in page


def test_monthly_report_with_no_activity_shows_zeros_and_a_note(client, manager):
    page = text(client.get("/platform/reports?type=monthly&month=3&year=2024"))
    assert "no activity" in page.lower()
    assert page.count("<td>0</td>") >= 6


def test_monthly_report_with_unreadable_month_asks_for_one(client, manager):
    page = text(client.get("/platform/reports?type=monthly&month=13&year=2026"))
    assert "Select a month and year" in page


def test_daily_report(client, manager, october):
    page = text(client.get("/platform/reports?type=daily&date=2026-10-10"))
    assert "<td>5</td>" in page
    assert "10 Oct 2026" in page
    assert "9 Oct 2026" in page or "09 Oct 2026" in page


def test_custom_report_and_bad_range(client, manager, october):
    page = text(client.get("/platform/reports?type=custom&startDate=2026-10-01&endDate=2026-10-31"))
    assert "<td>5</td>" in page
    page = text(client.get("/platform/reports?type=custom&startDate=2026-10-31&endDate=2026-10-01"))
    assert "The start date must not be after the end date" in page
    assert "IDP views" not in page


def test_pdf_download_headers(client, manager, october):
    resp = client.get("/platform/reports/pdf?type=monthly&month=10&year=2026")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.headers["Content-Disposition"] == "attachment; filename=activity_report_2026-10.pdf"
    assert resp.data.startswith(b"%PDF")
    daily = client.get("/platform/reports/pdf?type=daily&date=2026-10-10")
    assert "activity_report_2026-10-10.pdf" in daily.headers["Content-Disposition"]
    custom = client.get("/platform/reports/pdf?type=custom&startDate=2026-10-01&endDate=2026-10-31")
    assert "activity_report_2026-10-01_to_2026-10-31.pdf" in custom.headers["Content-Disposition"]


def test_pdf_with_bad_parameters_is_rejected(client, manager):
    assert client.get("/platform/reports/pdf?type=monthly&month=x&year=2026").status_code == 400
    assert client.get("/platform/reports/pdf?type=weekly").status_code == 400
    assert (
        client.get("/platform/reports/pdf?type=custom&startDate=2026-10-31&endDate=2026-10-01").status_code
        == 400
    )
