"""US-43, US-44 and US-46 entity methods: view count, shortlist count and the dashboard."""

from app.entity import IDPEntity


def test_getViewCount_returns_the_stored_counter(make_idp):
    idp = make_idp(viewCount=7)
    assert IDPEntity.getViewCount(idp.idpId) == 7


def test_getViewCount_is_zero_for_a_new_or_missing_idp(make_idp):
    idp = make_idp()
    assert IDPEntity.getViewCount(idp.idpId) == 0
    assert IDPEntity.getViewCount(99999) == 0


def test_getShortlistCount_returns_the_stored_counter(make_idp):
    idp = make_idp(shortlistCount=4)
    assert IDPEntity.getShortlistCount(idp.idpId) == 4
    assert IDPEntity.getShortlistCount(99999) == 0


def test_getInterestDashboard_groups_views_and_shortlists_by_style_and_category(
    make_account, make_category, make_idp
):
    designer = make_account(role="designer")
    other = make_account(role="designer")
    kitchen = make_category(name="Kitchen")
    bath = make_category(name="Bathroom")
    make_idp(designer, kitchen, title="A", style="Modern", viewCount=10, shortlistCount=2)
    make_idp(designer, kitchen, title="B", style="Modern", viewCount=5, shortlistCount=1)
    make_idp(designer, bath, title="C", style="Japandi", viewCount=3, shortlistCount=0)
    make_idp(designer, bath, title="Gone", style="Luxury", viewCount=99, status="Removed")
    make_idp(other, bath, title="Not mine", style="Luxury", viewCount=50)

    dashboard = IDPEntity.getInterestDashboard(designer.userId)

    assert dashboard["byStyle"] == [("Modern", 15, 3), ("Japandi", 3, 0)]
    assert dashboard["byCategory"] == [("Kitchen", 15, 3), ("Bathroom", 3, 0)]
    assert [idp.title for idp in dashboard["topIDPs"]] == ["A", "B", "C"]
    assert dashboard["maxValue"] == 15


def test_getInterestDashboard_top_idps_is_capped_at_five(make_account, make_category, make_idp):
    designer = make_account(role="designer")
    category = make_category()
    for n in range(7):
        make_idp(designer, category, title=f"P{n}", viewCount=n)
    top = IDPEntity.getInterestDashboard(designer.userId)["topIDPs"]
    assert [idp.title for idp in top] == ["P6", "P5", "P4", "P3", "P2"]


def test_getInterestDashboard_for_a_designer_without_projects(make_account):
    designer = make_account(role="designer")
    dashboard = IDPEntity.getInterestDashboard(designer.userId)
    assert dashboard == {"byStyle": [], "byCategory": [], "topIDPs": [], "maxValue": 0}
