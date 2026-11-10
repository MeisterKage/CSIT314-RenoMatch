"""US-58: ReportedIDPsPage at /platform/reported."""

import pytest

from app.entity import IDPEntity, IDPFlagEntity, db


@pytest.fixture
def manager(make_account, login):
    account = make_account(role="platform")
    login(account.username)
    return account


def add_flag(reporter, idp, reason="Stolen photos", status="Open"):
    flag = IDPFlagEntity(idpId=idp.idpId, reporterId=reporter.userId, reason=reason, status=status)
    db.session.add(flag)
    db.session.commit()
    return flag


def test_only_platform_managers_can_open_the_page(client, make_account, login):
    assert client.get("/platform/reported").status_code in (302, 401, 403)
    customer = make_account(role="customer")
    login(customer.username)
    assert client.get("/platform/reported").status_code in (302, 403)


def test_page_lists_open_flags_with_idp_and_reason(client, manager, make_account, make_idp):
    customer = make_account()
    add_flag(customer, make_idp(title="Reported loft"), "Stolen photos")
    add_flag(customer, make_idp(title="Old report"), "Spam", status="Dismissed")
    page = client.get("/platform/reported").data
    assert b"Reported loft" in page and b"Stolen photos" in page
    assert b"Old report" not in page
    assert b"Uphold" in page and b"Dismiss" in page and b"csrf_token" in page


def test_empty_state(client, manager):
    assert b"No reported" in client.get("/platform/reported").data


def test_uphold_removes_the_idp(client, manager, make_account, make_idp):
    idp = make_idp(isFeatured=True)
    flag = add_flag(make_account(), idp)
    response = client.post(f"/platform/reported/{flag.flagId}/uphold", follow_redirects=True)
    assert response.status_code == 200
    assert db.session.get(IDPEntity, idp.idpId).status == "Removed"
    assert db.session.get(IDPFlagEntity, flag.flagId).reviewedBy == manager.userId


def test_dismiss_keeps_the_idp(client, manager, make_account, make_idp):
    idp = make_idp()
    flag = add_flag(make_account(), idp)
    client.post(f"/platform/reported/{flag.flagId}/dismiss", follow_redirects=True)
    assert db.session.get(IDPEntity, idp.idpId).status == "Active"
    assert db.session.get(IDPFlagEntity, flag.flagId).status == "Dismissed"


def test_resolving_a_closed_report_shows_a_message(client, manager, make_account, make_idp):
    flag = add_flag(make_account(), make_idp(), status="Dismissed")
    response = client.post(f"/platform/reported/{flag.flagId}/uphold", follow_redirects=True)
    assert b"already" in response.data.lower()


def test_nav_links_to_both_pages(client, manager):
    page = client.get("/").data
    assert b'href="/platform/featured"' in page
    assert b'href="/platform/reported"' in page
