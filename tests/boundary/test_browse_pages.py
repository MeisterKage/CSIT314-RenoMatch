"""US-01, US-09, US-10, US-11: the browse, details and designer profile pages."""

from app.entity import CompanyInfoEntity, IDPEntity, ReviewEntity, db


def test_browse_is_public_and_shows_photo_cards(client, make_idp):
    make_idp(title="Sunny Tampines flat", photoUrls=["/static/img/idp/idp-01.jpg"])
    resp = client.get("/idps")
    assert resp.status_code == 200
    assert b"Sunny Tampines flat" in resp.data
    assert b"/static/img/idp/idp-01.jpg" in resp.data


def test_browse_hides_non_active(client, make_idp):
    make_idp(title="Visible one")
    make_idp(title="Hidden suspended", status="Suspended")
    make_idp(title="Hidden removed", status="Removed")
    page = client.get("/idps").data
    assert b"Visible one" in page
    assert b"Hidden suspended" not in page
    assert b"Hidden removed" not in page


def test_browse_paginates_at_24(client, make_idp, make_account, make_category):
    designer, category = make_account(role="designer"), make_category()
    for n in range(30):
        make_idp(designer=designer, category=category, title=f"Proj{n:02d}x")
    first = client.get("/idps").data
    second = client.get("/idps?page=2").data
    assert first.count(b'class="idp-card"') == 24
    assert second.count(b'class="idp-card"') == 6
    assert b"Page 1 of 2" in first


def test_browse_pagination_keeps_filters(client, make_idp, make_account, make_category):
    designer, category = make_account(role="designer"), make_category()
    for n in range(30):
        make_idp(designer=designer, category=category, style="Japandi")
    page = client.get("/idps?style=Japandi").data
    assert b"style=Japandi" in page
    assert b"page=2" in page


def test_browse_empty_message(client):
    assert b"No designs match your search" in client.get("/idps?keyword=zzz").data


def test_browse_filters(client, make_idp, make_category):
    category = make_category(name="Kitchens")
    make_idp(title="Keyword hit", description="has a pergola")
    make_idp(title="Category hit", category=category)
    make_idp(title="Style hit", style="Luxury")
    make_idp(title="Property hit", propertyType="Landed")
    make_idp(title="Budget hit", budget=99000.0)
    by_keyword = client.get("/idps?keyword=pergola").data
    assert b"Keyword hit" in by_keyword and b"Style hit" not in by_keyword
    by_category = client.get(f"/idps?category={category.categoryId}").data
    assert b"Category hit" in by_category and b"Keyword hit" not in by_category
    by_style = client.get("/idps?style=Luxury").data
    assert b"Style hit" in by_style and b"Keyword hit" not in by_style
    by_type = client.get("/idps?propertyType=Landed").data
    assert b"Property hit" in by_type and b"Keyword hit" not in by_type
    by_budget = client.get("/idps?minBudget=90000&maxBudget=100000").data
    assert b"Budget hit" in by_budget and b"Keyword hit" not in by_budget


def test_browse_ignores_bad_budget_values(client, make_idp):
    make_idp(title="Still listed")
    resp = client.get("/idps?minBudget=abc")
    assert resp.status_code == 200
    assert b"Still listed" in resp.data
    assert b"Enter budgets as numbers" in resp.data


def test_browse_rejects_min_above_max(client, make_idp):
    make_idp(title="Still listed")
    resp = client.get("/idps?minBudget=500&maxBudget=100")
    assert b"Minimum budget cannot be above the maximum" in resp.data
    assert b"Still listed" in resp.data


def test_browse_ignores_bad_page_number(client, make_idp):
    make_idp()
    assert client.get("/idps?page=abc").status_code == 200


def test_browse_filter_form_lists_active_categories_only(client, make_category):
    make_category(name="Open category")
    make_category(name="Closed category", status="Suspended")
    page = client.get("/idps").data
    assert b"Open category" in page
    assert b"Closed category" not in page


def test_home_style_cards_link_to_filtered_browse(client):
    page = client.get("/").data
    assert b"/idps?style=Japandi" in page
    assert b"/idps?style=Mid-Century" in page


def test_nav_has_browse_designs_link(client):
    assert b"Browse designs" in client.get("/").data


def test_details_page_shows_idp_and_designer_link(client, make_idp):
    idp = make_idp(
        title="Calm bedroom",
        description="Soft timber tones",
        photoUrls=["/static/img/idp/idp-02.jpg", "/static/img/idp/idp-03.jpg"],
    )
    resp = client.get(f"/idps/{idp.idpId}")
    assert resp.status_code == 200
    for text in (b"Calm bedroom", b"Soft timber tones", b"Tampines", b"45,000"):
        assert text in resp.data
    assert b"/static/img/idp/idp-03.jpg" in resp.data
    assert f"/designers/{idp.designerId}".encode() in resp.data


def test_details_page_has_compare_form(client, make_idp):
    idp = make_idp()
    page = client.get(f"/idps/{idp.idpId}").data
    assert b'action="/compare/select"' in page
    assert b'name="idpId"' in page


def test_details_counts_customer_view_but_not_designer(client, make_idp, make_account, login):
    make_account(username="cust")
    idp = make_idp()
    designer_username = idp.designer.username
    idpId = idp.idpId
    login("cust")
    client.get(f"/idps/{idpId}")
    client.get(f"/idps/{idpId}")
    assert db.session.get(IDPEntity, idpId).viewCount == 2
    client.post("/logout")
    login(designer_username)
    client.get(f"/idps/{idpId}")
    assert db.session.get(IDPEntity, idpId).viewCount == 2


def test_details_counts_visitor_view(client, make_idp):
    idp = make_idp()
    client.get(f"/idps/{idp.idpId}")
    assert db.session.get(IDPEntity, idp.idpId).viewCount == 1


def test_details_404_for_non_active_and_unknown(client, make_idp):
    suspended = make_idp(status="Suspended")
    removed = make_idp(status="Removed")
    assert client.get(f"/idps/{suspended.idpId}").status_code == 404
    assert client.get(f"/idps/{removed.idpId}").status_code == 404
    assert client.get("/idps/9999").status_code == 404
    assert db.session.get(IDPEntity, suspended.idpId).viewCount == 0


def test_designer_profile_shows_company_portfolio_and_rating(client, make_idp, make_account):
    designer = make_account(role="designer", name="Dana Designer")
    db.session.add(
        CompanyInfoEntity(designerId=designer.userId, name="Studio X", description="We build")
    )
    db.session.add(
        ReviewEntity(
            designerId=designer.userId,
            userId=make_account(name="Rita Reviewer").userId,
            rating=5,
            comment="Superb work",
        )
    )
    db.session.add(
        ReviewEntity(
            designerId=designer.userId, userId=make_account().userId, rating=4, comment="Good"
        )
    )
    db.session.commit()
    make_idp(designer=designer, title="Portfolio piece")
    make_idp(designer=designer, title="Gone piece", status="Removed")
    resp = client.get(f"/designers/{designer.userId}")
    assert resp.status_code == 200
    for text in (b"Studio X", b"We build", b"Portfolio piece", b"Superb work", b"Rita Reviewer"):
        assert text in resp.data
    assert b"Gone piece" not in resp.data
    assert b"4.5" in resp.data
    assert b"2 reviews" in resp.data


def test_designer_profile_without_reviews_or_company(client, make_account):
    designer = make_account(role="designer", name="New Designer")
    resp = client.get(f"/designers/{designer.userId}")
    assert resp.status_code == 200
    assert b"New Designer" in resp.data
    assert b"No reviews yet" in resp.data


def test_designer_profile_404(client, make_account):
    customer = make_account()
    suspended = make_account(role="designer", status="Suspended")
    assert client.get(f"/designers/{customer.userId}").status_code == 404
    assert client.get(f"/designers/{suspended.userId}").status_code == 404
    assert client.get("/designers/9999").status_code == 404
