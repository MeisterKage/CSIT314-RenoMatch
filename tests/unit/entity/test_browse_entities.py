"""US-01, US-09, US-10, US-11: entity methods behind browsing."""

from app.entity import (
    CompanyInfoEntity,
    IDPEntity,
    PlatformActivityEntity,
    ReviewEntity,
    db,
)


def test_get_active_idps_lists_only_active(make_idp):
    active = make_idp(title="Active one")
    make_idp(title="Suspended one", status="Suspended")
    make_idp(title="Removed one", status="Removed")
    page = IDPEntity.getActiveIDPs(1)
    assert [idp.idpId for idp in page.items] == [active.idpId]


def test_get_active_idps_paginates_at_24_newest_first(make_idp, make_account, make_category):
    designer, category = make_account(role="designer"), make_category()
    for n in range(30):
        make_idp(designer=designer, category=category, title=f"Project {n}")
    first, second = IDPEntity.getActiveIDPs(1), IDPEntity.getActiveIDPs(2)
    assert len(first.items) == 24
    assert len(second.items) == 6
    assert first.pages == 2
    assert first.items[0].title == "Project 29"


def test_search_keyword_matches_title_or_description(make_idp):
    a = make_idp(title="Bright Japandi flat", description="plain")
    b = make_idp(title="Other", description="A japandi bedroom")
    make_idp(title="Unrelated", description="nothing")
    found = IDPEntity.searchIDPs("JAPANDI", None, None, None, None, None)
    assert {idp.idpId for idp in found.items} == {a.idpId, b.idpId}


def test_search_by_category(make_idp, make_category):
    wanted = make_category()
    hit = make_idp(category=wanted)
    make_idp()
    found = IDPEntity.searchIDPs(None, wanted.categoryId, None, None, None, None)
    assert [idp.idpId for idp in found.items] == [hit.idpId]


def test_search_by_style(make_idp):
    hit = make_idp(style="Japandi")
    make_idp(style="Luxury")
    found = IDPEntity.searchIDPs(None, None, "Japandi", None, None, None)
    assert [idp.idpId for idp in found.items] == [hit.idpId]


def test_search_by_property_type(make_idp):
    hit = make_idp(propertyType="Landed")
    make_idp(propertyType="HDB")
    found = IDPEntity.searchIDPs(None, None, None, "Landed", None, None)
    assert [idp.idpId for idp in found.items] == [hit.idpId]


def test_search_by_budget_range_is_inclusive(make_idp):
    low = make_idp(budget=10000.0)
    mid = make_idp(budget=20000.0)
    high = make_idp(budget=30000.0)
    both = IDPEntity.searchIDPs(None, None, None, None, 10000.0, 20000.0)
    assert {idp.idpId for idp in both.items} == {low.idpId, mid.idpId}
    only_min = IDPEntity.searchIDPs(None, None, None, None, 20000.0, None)
    assert {idp.idpId for idp in only_min.items} == {mid.idpId, high.idpId}
    only_max = IDPEntity.searchIDPs(None, None, None, None, None, 10000.0)
    assert [idp.idpId for idp in only_max.items] == [low.idpId]


def test_search_combines_filters_and_skips_non_active(make_idp):
    hit = make_idp(style="Modern", propertyType="HDB")
    make_idp(style="Modern", propertyType="HDB", status="Suspended")
    make_idp(style="Modern", propertyType="Landed")
    found = IDPEntity.searchIDPs(None, None, "Modern", "HDB", None, None)
    assert [idp.idpId for idp in found.items] == [hit.idpId]


def test_search_with_blank_filters_returns_all_active(make_idp):
    make_idp()
    make_idp()
    assert len(IDPEntity.searchIDPs("", None, "", "", None, None).items) == 2


def test_record_view_counts_a_customer_view(make_idp, make_account):
    idp = make_idp()
    customer = make_account()
    result = IDPEntity.recordView(idp.idpId, customer.userId)
    assert result.idpId == idp.idpId
    assert result.viewCount == 1
    rows = PlatformActivityEntity.query.filter_by(activityType="view", idpId=idp.idpId).all()
    assert [row.userId for row in rows] == [customer.userId]


def test_record_view_counts_an_anonymous_view(make_idp):
    idp = make_idp()
    IDPEntity.recordView(idp.idpId, None)
    assert db.session.get(IDPEntity, idp.idpId).viewCount == 1
    row = PlatformActivityEntity.query.filter_by(idpId=idp.idpId).one()
    assert row.userId is None


def test_record_view_ignores_the_owning_designer(make_idp):
    idp = make_idp()
    result = IDPEntity.recordView(idp.idpId, idp.designerId)
    assert result.idpId == idp.idpId
    assert result.viewCount == 0
    assert PlatformActivityEntity.query.count() == 0


def test_record_view_returns_none_unless_active(make_idp):
    suspended = make_idp(status="Suspended")
    removed = make_idp(status="Removed")
    assert IDPEntity.recordView(suspended.idpId, None) is None
    assert IDPEntity.recordView(removed.idpId, None) is None
    assert IDPEntity.recordView(9999, None) is None
    assert PlatformActivityEntity.query.count() == 0


def test_get_active_by_designer(make_idp, make_account):
    designer = make_account(role="designer")
    hit = make_idp(designer=designer)
    make_idp(designer=designer, status="Removed")
    make_idp()
    assert [idp.idpId for idp in IDPEntity.getActiveByDesigner(designer.userId)] == [hit.idpId]


def _review(designer, user, rating, comment=""):
    db.session.add(
        ReviewEntity(designerId=designer.userId, userId=user.userId, rating=rating, comment=comment)
    )
    db.session.commit()


def test_average_rating(make_account):
    designer = make_account(role="designer")
    assert ReviewEntity.getAverageRating(designer.userId) == 0.0
    _review(designer, make_account(), 5)
    _review(designer, make_account(), 4)
    assert ReviewEntity.getAverageRating(designer.userId) == 4.5


def test_get_reviews_newest_first(make_account):
    designer = make_account(role="designer")
    _review(designer, make_account(), 5, "first")
    _review(designer, make_account(), 3, "second")
    assert [r.comment for r in ReviewEntity.getReviews(designer.userId)] == ["second", "first"]


def test_company_info_find_by_designer(make_account):
    designer = make_account(role="designer")
    assert CompanyInfoEntity.findByDesignerId(designer.userId) is None
    db.session.add(CompanyInfoEntity(designerId=designer.userId, name="Studio X"))
    db.session.commit()
    assert CompanyInfoEntity.findByDesignerId(designer.userId).name == "Studio X"
