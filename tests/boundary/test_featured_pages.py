"""US-60 (diagrammed): ManageFeaturedIDPsPage at /platform/featured."""

import re

import pytest

from app.boundary.moderation import ManageFeaturedIDPsPage
from app.control.feature_idp_controller import FeatureIDPController
from app.entity import IDPEntity, db


@pytest.fixture
def manager(make_account, login):
    account = make_account(role="platform")
    login(account.username)
    return account


def test_page_holds_the_feature_controller_as_controller(app):
    assert isinstance(ManageFeaturedIDPsPage().controller, FeatureIDPController)


def test_only_platform_managers_can_open_the_page(client, make_account, login):
    assert client.get("/platform/featured").status_code in (302, 401, 403)
    customer = make_account(role="customer")
    login(customer.username)
    assert client.get("/platform/featured").status_code in (302, 403)


def test_page_lists_featured_slots_and_active_idps_with_buttons(client, manager, make_idp):
    make_idp(title="Featured loft", isFeatured=True)
    make_idp(title="Plain nook")
    make_idp(title="Hidden removed", status="Removed")
    page = client.get("/platform/featured").data
    assert b"Featured loft" in page and b"Plain nook" in page
    assert b"Hidden removed" not in page
    assert b">Feature<" in page and b">Unfeature<" in page
    assert b"csrf_token" in page


def test_search_filters_the_list(client, manager, make_idp):
    make_idp(title="Alpine chalet")
    make_idp(title="Urban studio")
    page = client.get("/platform/featured?keyword=alpine").data
    assert b"Alpine chalet" in page
    assert b"Urban studio" not in page


def test_list_is_paginated(client, manager, make_idp):
    for n in range(26):
        make_idp(title=f"Design {n:02d}")
    assert b"Page 1 of 2" in client.get("/platform/featured").data
    assert b"Page 2 of 2" in client.get("/platform/featured?page=2").data


def test_feature_success_shows_success_and_updates_the_home_page(client, manager, make_idp):
    idp = make_idp(title="Sunny penthouse")
    response = client.post(f"/platform/featured/{idp.idpId}/feature", follow_redirects=True)
    assert b"is now featured" in response.data
    assert db.session.get(IDPEntity, idp.idpId).isFeatured is True
    assert b"Sunny penthouse" in client.get("/").data


def test_unfeature_success_removes_it_from_the_home_page(client, manager, make_idp):
    idp = make_idp(title="Sunny penthouse", isFeatured=True)
    client.post(f"/platform/featured/{idp.idpId}/unfeature", follow_redirects=True)
    assert db.session.get(IDPEntity, idp.idpId).isFeatured is False
    assert b"Sunny penthouse" not in client.get("/").data


def test_seventh_feature_is_refused_with_the_limit_message(client, manager, make_idp):
    for _ in range(6):
        make_idp(isFeatured=True)
    idp = make_idp()
    response = client.post(f"/platform/featured/{idp.idpId}/feature", follow_redirects=True)
    assert b"Maximum of 6 featured IDPs. Unfeature one first" in response.data
    assert db.session.get(IDPEntity, idp.idpId).isFeatured is False


def test_suspended_idp_is_refused_with_its_own_message(client, manager, make_idp):
    idp = make_idp(status="Suspended")
    response = client.post(f"/platform/featured/{idp.idpId}/feature", follow_redirects=True)
    assert b"suspended or removed" in response.data
    assert b"Maximum of 6" not in response.data


def test_boundary_calls_follow_the_sequence_diagram(client, manager, make_idp, monkeypatch):
    calls = []
    for name in ("displaySuccess", "displayMessage"):
        function = getattr(ManageFeaturedIDPsPage, name)

        def spy(self, function=function, name=name):
            calls.append(name)
            return function(self)

        monkeypatch.setattr(ManageFeaturedIDPsPage, name, spy)
    good = make_idp()
    suspended = make_idp(status="Suspended")
    client.post(f"/platform/featured/{good.idpId}/feature")  # 1.2
    client.post(f"/platform/featured/{suspended.idpId}/feature")  # 1.3
    for _ in range(5):
        make_idp(isFeatured=True)
    client.post(f"/platform/featured/{make_idp().idpId}/feature")  # 1.4
    client.post(f"/platform/featured/{good.idpId}/unfeature")  # 2.2
    assert calls == ["displaySuccess", "displayMessage", "displayMessage", "displaySuccess"]


def test_forms_need_a_csrf_token(app, make_account, make_idp):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    manager = make_account(role="platform")
    idp = make_idp()
    page = client.get("/login").data
    token = re.search(rb'name="csrf_token" value="([^"]+)"', page).group(1).decode()
    client.post(
        "/login", data={"username": manager.username, "password": "Passw0rd!", "csrf_token": token}
    )
    assert client.post(f"/platform/featured/{idp.idpId}/feature").status_code == 400
