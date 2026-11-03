"""US-35, US-36, US-37: the company info page."""

from app.entity import CompanyInfoEntity

FORM = {
    "name": "Studio Oak",
    "description": "Calm homes.",
    "address": "1 Orchard Road",
    "phone": "+65 6123 4567",
    "email": "hello@oak.sg",
    "website": "https://oak.sg",
}


def designer_login(make_account, login):
    account = make_account(role="designer")
    login(account.username)
    return account


def test_requires_designer(client, make_account, login):
    assert client.get("/designer/company").status_code == 302
    login(make_account(role="customer").username)
    assert client.get("/designer/company").status_code == 403


def test_empty_state_shows_create_form(client, make_account, login):
    designer_login(make_account, login)
    page = client.get("/designer/company").data
    assert b"Add your company information" in page
    assert b'name="website"' in page


def test_create_then_view_with_edit_form(client, make_account, login):
    designer = designer_login(make_account, login)
    resp = client.post("/designer/company", data=FORM)
    assert resp.status_code == 302
    assert CompanyInfoEntity.query.filter_by(designerId=designer.userId).one().name == "Studio Oak"
    page = client.get("/designer/company").data
    assert b"Studio Oak" in page
    assert b"Save changes" in page


def test_update_existing(client, make_account, login):
    designer_login(make_account, login)
    client.post("/designer/company", data=FORM)
    client.post("/designer/company", data={**FORM, "name": "Oak and Pine"})
    assert CompanyInfoEntity.query.count() == 1
    assert CompanyInfoEntity.query.one().name == "Oak and Pine"


def test_validation_errors_are_shown_and_nothing_saved(client, make_account, login):
    designer_login(make_account, login)
    resp = client.post("/designer/company", data={**FORM, "name": "", "email": "bad"})
    assert resp.status_code == 200
    assert b"Enter your company name." in resp.data
    assert b"Enter a valid email address." in resp.data
    assert CompanyInfoEntity.query.count() == 0


def test_nav_and_home_link_to_company(client, make_account, login):
    designer_login(make_account, login)
    for page in (client.get("/designer/").data, client.get("/designer/company").data):
        assert b'href="/designer/company"' in page
