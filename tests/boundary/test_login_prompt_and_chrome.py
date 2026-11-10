import re
from pathlib import Path

import pytest

TEMPLATES = Path(__file__).parents[2] / "app" / "boundary" / "templates"


def nav_of(page: bytes) -> str:
    """The contents of the main navigation in a rendered page."""
    return re.search(r'<nav class="site-nav".*?</nav>', page.decode(), re.S).group(0)


def test_visitor_is_prompted_to_log_in_to_compare(client, make_idp):
    page = client.get(f"/idps/{make_idp().idpId}").data.decode()
    assert 'id="login-prompt"' in page
    assert "Log in to compare designs" in page
    assert re.search(r'<a[^>]*href="/login"[^>]*data-login-prompt', page)
    assert 'action="/compare/select"' not in page


def test_customer_gets_the_compare_form_not_the_prompt(client, make_account, make_idp, login):
    idp = make_idp()
    login(make_account(role="customer").username)
    page = client.get(f"/idps/{idp.idpId}").data.decode()
    assert 'action="/compare/select"' in page
    assert 'id="login-prompt"' not in page


def test_other_roles_get_neither_compare_control(client, make_account, make_idp, login):
    idp = make_idp()
    login(make_account(role="admin").username)
    page = client.get(f"/idps/{idp.idpId}").data.decode()
    assert 'action="/compare/select"' not in page
    assert 'id="login-prompt"' not in page


def test_visitor_cannot_use_compare_without_logging_in(client, make_idp):
    idp = make_idp()
    for resp in (client.get("/compare"), client.post("/compare/select", data={"idpId": idp.idpId})):
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/login"


@pytest.mark.parametrize(
    "role, home",
    [
        ("admin", "/admin/"),
        ("designer", "/"),
        ("customer", "/"),
        ("platform", "/"),
    ],
)
def test_nav_shows_account_name_beside_log_out_and_no_home_tab(
    client, make_account, login, role, home
):
    login(make_account(role=role, name="Dana Tan").username)
    nav = nav_of(client.get(home).data)
    assert ">Account<" not in nav
    assert ">Home<" not in nav
    assert re.search(r'href="/account/?"[^>]*>\s*Dana Tan\s*</a>\s*<form[^>]*logout', nav)


def test_footer_has_no_project_note(client):
    page = client.get("/").data
    assert b"group project" not in page
    assert b"Test data is regenerated" not in page


def test_role_home_only_greets(client, make_account, login):
    login(make_account(role="admin", name="Dana Tan").username)
    page = client.get("/admin/").data
    assert b"Welcome, Dana Tan." in page
    assert b"what you can do" not in page


def test_page_headings_have_no_side_text():
    heads = []
    for template in TEMPLATES.rglob("*.html"):
        for head in re.findall(
            r'<div class="section-head">.*?</div>', template.read_text(encoding="utf-8"), re.S
        ):
            if "<p" in head:
                heads.append(f"{template.name}: {head}")
    assert heads == []
