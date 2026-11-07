"""US-38 to US-42: the portfolio pages, add form, edit form, delete and photo serving."""

from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.test import EnvironBuilder

from app.entity import CompanyInfoEntity, IDPEntity, PlatformActivityEntity, db
from tests.helpers import GIF_BYTES, jpeg_bytes, png_bytes

MB = 1024 * 1024


def photo(name="room.png", data=None):
    return (BytesIO(data if data is not None else png_bytes()), name)


@pytest.fixture
def designer(make_account, login):
    account = make_account(role="designer")
    login(account.username)
    return account


@pytest.fixture
def company(designer):
    db.session.add(CompanyInfoEntity(designerId=designer.userId, name="Studio Oak"))
    db.session.commit()


@pytest.fixture
def category(make_category):
    return make_category(name="Kitchens")


@pytest.fixture
def form(category):
    def _form(photos=None, **fields):
        values = {
            "title": "Bright kitchen",
            "description": "Open plan.",
            "categoryId": str(category.categoryId),
            "style": "Modern",
            "propertyType": "HDB",
            "budget": "30000",
            "location": "Bishan",
            "photos": [photo()] if photos is None else photos,
        }
        values.update(fields)
        return values

    return _form


def submit(client, url, data):
    """POST a multipart form, closing the temporary file the test client spools it to."""
    builder = EnvironBuilder(
        path=url, method="POST", data=data, content_type="multipart/form-data"
    )
    environ = builder.get_environ()
    try:
        return client.open(environ)
    finally:
        environ["wsgi.input"].close()
        builder.close()


def uploads(app):
    folder = Path(app.config["UPLOAD_FOLDER"])
    return sorted(folder.iterdir()) if folder.exists() else []


# --- access, list, search (US-42) ---


def test_portfolio_requires_a_designer(client, make_account, login):
    assert client.get("/designer/portfolio").status_code == 302
    login(make_account(role="customer").username)
    assert client.get("/designer/portfolio").status_code == 403


def test_empty_portfolio_offers_add(client, designer):
    page = client.get("/designer/portfolio").data
    assert b"+ Add IDP" in page
    assert b'href="/designer/portfolio/new"' in page
    assert b"You have no projects yet" in page


def test_lists_own_idps_with_status_and_photo_but_not_removed_or_others(
    client, designer, make_idp, make_account
):
    make_idp(designer=designer, title="Mine active", photoUrls=["/uploads/a.png"])
    make_idp(designer=designer, title="Mine suspended", status="Suspended")
    make_idp(designer=designer, title="Mine removed", status="Removed")
    make_idp(designer=make_account(role="designer"), title="Someone else")
    page = client.get("/designer/portfolio").data.decode()
    assert "Mine active" in page and "Mine suspended" in page
    assert "Mine removed" not in page and "Someone else" not in page
    assert 'src="/uploads/a.png"' in page
    assert "badge" in page and "Suspended" in page and "Active" in page


def test_search_filters_own_idps(client, designer, make_idp):
    make_idp(designer=designer, title="Calm study")
    make_idp(designer=designer, title="Loud kitchen")
    page = client.get("/designer/portfolio?keyword=calm").data.decode()
    assert "Calm study" in page and "Loud kitchen" not in page
    assert "No projects match your search" in client.get(
        "/designer/portfolio?keyword=zzz"
    ).data.decode()
    assert 'name="keyword"' in page


# --- US-38 add form ---


def test_add_form_needs_company_info_first(client, designer, form, app):
    page = client.get("/designer/portfolio/new").data.decode()
    assert "Add your company information before you add a project" in page
    assert 'href="/designer/company"' in page
    assert 'type="file"' not in page
    resp = submit(client, "/designer/portfolio/new", form())
    assert "company information" in resp.data.decode()
    assert IDPEntity.query.count() == 0
    assert uploads(app) == []


def test_add_form_shows_fields_and_only_active_categories(
    client, designer, company, category, make_category
):
    make_category(name="Hidden bathrooms", status="Suspended")
    page = client.get("/designer/portfolio/new").data.decode()
    assert 'enctype="multipart/form-data"' in page
    assert 'name="photos"' in page and "multiple" in page
    for name in ("title", "description", "categoryId", "style", "propertyType", "budget",
                 "location"):
        assert f'name="{name}"' in page
    assert "Kitchens" in page and "Hidden bathrooms" not in page


def test_add_valid_idp_saves_photos_and_redirects(client, designer, company, form, app):
    resp = submit(client, "/designer/portfolio/new",
                  form([photo(), photo("b.jpeg", jpeg_bytes())]))
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/designer/portfolio")
    idp = IDPEntity.query.one()
    assert idp.designerId == designer.userId and idp.title == "Bright kitchen"
    assert len(idp.photoUrls) == 2 and all(u.startswith("/uploads/") for u in idp.photoUrls)
    saved = uploads(app)
    assert len(saved) == 2
    assert {f"/uploads/{f.name}" for f in saved} == set(idp.photoUrls)
    assert PlatformActivityEntity.query.filter_by(activityType="idp_added").count() == 1
    listing = client.get("/designer/portfolio").data.decode()
    assert "Bright kitchen" in listing and "Your project has been added." in listing


def test_6a_missing_fields_shows_message_keeps_values_and_saves_nothing(
    client, designer, company, form, app
):
    data = form(title="", location="", description="Kept")
    resp = submit(client, "/designer/portfolio/new", data)
    page = resp.data.decode()
    assert resp.status_code == 200
    assert "required fields" in page and "Title" in page and "Location" in page
    assert "Kept" in page
    assert IDPEntity.query.count() == 0 and uploads(app) == []


def test_6a_no_photo_is_reported(client, designer, company, form):
    resp = submit(client, "/designer/portfolio/new", form([]))
    assert "Photos" in resp.data.decode()
    assert IDPEntity.query.count() == 0


@pytest.mark.parametrize(
    "bad",
    [
        lambda: photo("x.gif", GIF_BYTES),
        lambda: photo("x.png", b"plain text pretending"),
        lambda: photo("x.png", png_bytes(5 * MB + 1)),
    ],
)
def test_6b_invalid_photo_shows_message_and_saves_nothing(
    client, designer, company, form, app, bad
):
    resp = submit(client, "/designer/portfolio/new", form([photo(), bad()]))
    page = resp.data.decode()
    assert resp.status_code == 200
    assert "JPG or PNG" in page and "5 MB" in page
    assert IDPEntity.query.count() == 0 and uploads(app) == []


def test_6c_suspended_category_asks_for_another(
    client, designer, company, form, category, app
):
    category.status = "Suspended"
    db.session.commit()
    resp = submit(client, "/designer/portfolio/new", form())
    assert "category is suspended" in resp.data.decode()
    assert IDPEntity.query.count() == 0 and uploads(app) == []


def test_request_over_the_total_limit_is_refused_with_a_message(
    client, designer, company, form, app
):
    assert app.config["MAX_CONTENT_LENGTH"] == 30 * MB
    big = [photo(f"{n}.png", png_bytes(10 * MB)) for n in range(4)]
    resp = submit(client, "/designer/portfolio/new", form(big))
    assert resp.status_code in (302, 413)
    assert IDPEntity.query.count() == 0


# --- serving uploads ---


def test_uploaded_photo_is_served_and_unsafe_paths_are_not(client, designer, company, form):
    submit(client, "/designer/portfolio/new", form())
    url = IDPEntity.query.one().photoUrls[0]
    with client.get(url) as resp:
        assert resp.status_code == 200 and resp.mimetype == "image/png"
        assert resp.data == png_bytes()
    assert client.get("/uploads/missing.png").status_code == 404
    assert client.get("/uploads/..%2Frenomatch.db").status_code == 404
    assert client.get("/uploads/../../app/__init__.py").status_code == 404


# --- US-39 details ---


def test_details_page_shows_own_idp(client, designer, make_idp):
    idp = make_idp(designer=designer, title="My loft", photoUrls=["/uploads/a.png"])
    page = client.get(f"/designer/portfolio/{idp.idpId}").data.decode()
    assert "My loft" in page and "/uploads/a.png" in page and "Active" in page
    assert f"/designer/portfolio/{idp.idpId}/edit" in page
    assert f"/designer/portfolio/{idp.idpId}/delete" in page


def test_details_of_another_designers_or_removed_idp_is_not_found(
    client, designer, make_idp, make_account
):
    theirs = make_idp(designer=make_account(role="designer"))
    gone = make_idp(designer=designer, status="Removed")
    assert client.get(f"/designer/portfolio/{theirs.idpId}").status_code == 404
    assert client.get(f"/designer/portfolio/{gone.idpId}").status_code == 404
    assert client.get("/designer/portfolio/9999").status_code == 404


# --- US-40 edit ---


def add_one(client, form, **fields):
    submit(client, "/designer/portfolio/new", form(**fields))
    return IDPEntity.query.order_by(IDPEntity.idpId.desc()).first()


def test_edit_form_is_prefilled_with_photos(client, designer, company, form):
    idp = add_one(client, form)
    page = client.get(f"/designer/portfolio/{idp.idpId}/edit").data.decode()
    assert 'value="Bright kitchen"' in page
    assert 'name="removePhotos"' in page and idp.photoUrls[0] in page
    assert 'name="photos"' in page


def test_edit_updates_details_adds_and_removes_photos(client, designer, company, form, app):
    idp = add_one(client, form, photos=[photo(), photo("b.png")])
    first, second = idp.photoUrls
    data = form([photo("c.png")], title="Renamed", removePhotos=[first])
    resp = submit(client, f"/designer/portfolio/{idp.idpId}/edit", data)
    assert resp.status_code == 302
    idp = db.session.get(IDPEntity, idp.idpId)
    assert idp.title == "Renamed"
    assert len(idp.photoUrls) == 2 and second in idp.photoUrls and first not in idp.photoUrls
    assert len(uploads(app)) == 2


def test_edit_cannot_remove_every_photo(client, designer, company, form):
    idp = add_one(client, form)
    data = form([], removePhotos=list(idp.photoUrls))
    resp = submit(client, f"/designer/portfolio/{idp.idpId}/edit", data)
    assert resp.status_code == 200 and "Photos" in resp.data.decode()
    assert len(db.session.get(IDPEntity, idp.idpId).photoUrls) == 1


def test_edit_shows_each_message(client, designer, company, form, make_category):
    idp = add_one(client, form)
    url = f"/designer/portfolio/{idp.idpId}/edit"
    assert "required fields" in submit(client, url, form([], title="")).data.decode()
    assert "JPG or PNG" in submit(client, url, form([photo("g.gif", GIF_BYTES)])).data.decode()
    suspended = make_category(name="Closed", status="Suspended")
    moved = form([], categoryId=str(suspended.categoryId))
    assert "category is suspended" in submit(client, url, moved).data.decode()
    assert db.session.get(IDPEntity, idp.idpId).title == "Bright kitchen"


def test_edit_of_another_designers_idp_is_not_found(
    client, designer, company, form, make_idp, make_account
):
    theirs = make_idp(designer=make_account(role="designer"), title="Theirs")
    url = f"/designer/portfolio/{theirs.idpId}/edit"
    assert client.get(url).status_code == 404
    assert submit(client, url, form(title="Hacked")).status_code == 404
    assert db.session.get(IDPEntity, theirs.idpId).title == "Theirs"


# --- US-41 delete ---


def test_delete_removes_from_portfolio_and_public_pages(client, designer, make_idp):
    idp = make_idp(designer=designer, title="Doomed", isFeatured=True)
    resp = client.post(f"/designer/portfolio/{idp.idpId}/delete")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/designer/portfolio")
    idp = db.session.get(IDPEntity, idp.idpId)
    assert idp.status == "Removed" and idp.isFeatured is False
    assert "Doomed" not in client.get("/designer/portfolio").data.decode()
    assert client.get(f"/idps/{idp.idpId}").status_code == 404
    assert "Doomed" not in client.get("/idps").data.decode()
    assert "Doomed" not in client.get("/").data.decode()


def test_delete_of_another_designers_idp_is_refused(client, designer, make_idp, make_account):
    theirs = make_idp(designer=make_account(role="designer"), title="Theirs", isFeatured=True)
    assert client.post(f"/designer/portfolio/{theirs.idpId}/delete").status_code == 404
    theirs = db.session.get(IDPEntity, theirs.idpId)
    assert theirs.status == "Active" and theirs.isFeatured is True


def test_delete_is_post_only(client, designer, make_idp):
    idp = make_idp(designer=designer)
    assert client.get(f"/designer/portfolio/{idp.idpId}/delete").status_code == 405


# --- navigation ---


def test_nav_and_home_link_to_the_portfolio(client, designer):
    for page in (client.get("/").data, client.get("/designer/portfolio").data):
        assert b'href="/designer/portfolio"' in page


# --- US-38 sequence: which display method each branch calls (steps 1.2 to 1.5) ---


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, "displaySuccess"),
        ({"title": ""}, "displayMessage"),
        ({"photos": [("gif", "x.gif")]}, "displayMessage"),
    ],
)
def test_each_branch_calls_one_display_method(
    client, designer, company, form, monkeypatch, changes, expected
):
    from app.boundary.portfolio import MyPortfolioPage

    called = []
    for name in ("displaySuccess", "displayMessage"):
        original = getattr(MyPortfolioPage, name)

        def spy(self, _name=name, _original=original):
            called.append(_name)
            return _original(self)

        monkeypatch.setattr(MyPortfolioPage, name, spy)
    data = form(**changes)
    if "photos" in changes:
        data["photos"] = [photo("x.gif", GIF_BYTES)]
    submit(client, "/designer/portfolio/new", data)
    assert called == [expected]


def test_suspended_category_calls_display_message_once(
    client, designer, company, form, category, monkeypatch
):
    from app.boundary.portfolio import MyPortfolioPage

    called = []
    original = MyPortfolioPage.displayMessage
    monkeypatch.setattr(
        MyPortfolioPage, "displayMessage", lambda self: called.append(1) or original(self)
    )
    category.status = "Suspended"
    db.session.commit()
    submit(client, "/designer/portfolio/new", form())
    assert called == [1]
