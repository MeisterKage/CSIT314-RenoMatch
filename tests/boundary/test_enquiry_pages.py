"""US-18, US-47: the enquiry form, the designer inbox and the customer threads."""

import pytest

from app.entity import EnquiryEntity, PlatformActivityEntity


@pytest.fixture
def scene(make_account, make_idp):
    designer = make_account(role="designer")
    customer = make_account()
    idp = make_idp(designer=designer)
    return designer, customer, idp


def send(client, idp, **data):
    payload = {"subject": "Price", "message": "How much?"}
    payload.update(data)
    return client.post(f"/idps/{idp.idpId}/enquiry", data=payload)


def test_details_page_shows_enquiry_form_to_customers_only(client, scene, login):
    _, customer, idp = scene
    assert f"/idps/{idp.idpId}/enquiry".encode() not in client.get(f"/idps/{idp.idpId}").data
    login(customer.username)
    page = client.get(f"/idps/{idp.idpId}").data
    assert f"/idps/{idp.idpId}/enquiry".encode() in page
    assert b'name="subject"' in page and b'name="message"' in page


def test_send_enquiry_creates_thread_and_redirects_to_it(client, scene, login):
    _, customer, idp = scene
    login(customer.username)
    resp = send(client, idp)
    enquiry = EnquiryEntity.query.one()
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/enquiries/{enquiry.enquiryId}")
    assert PlatformActivityEntity.query.filter_by(activityType="enquiry").count() == 1


def test_send_enquiry_needs_a_customer(client, scene, login):
    designer, _, idp = scene
    assert send(client, idp).status_code == 302
    login(designer.username)
    assert send(client, idp).status_code == 403
    assert EnquiryEntity.query.count() == 0


@pytest.mark.parametrize("data", [{"subject": ""}, {"message": " "}, {"subject": "s" * 151}])
def test_send_enquiry_invalid_input_stores_nothing(client, scene, login, data):
    _, customer, idp = scene
    login(customer.username)
    resp = send(client, idp, **data)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/idps/{idp.idpId}")
    assert EnquiryEntity.query.count() == 0


def test_send_enquiry_to_unknown_idp_is_404(client, scene, login):
    _, customer, _ = scene
    login(customer.username)
    assert client.post("/idps/9999/enquiry", data={"subject": "a", "message": "b"}).status_code == 404


def test_designer_inbox_lists_their_enquiries(client, scene, login, make_account, make_idp):
    designer, customer, idp = scene
    login(customer.username)
    send(client, idp, subject="Kitchen question")
    other = make_idp()
    send(client, other, subject="Not yours")
    client.post("/logout")
    login(designer.username)
    page = client.get("/designer/enquiries").data
    assert b"Kitchen question" in page
    assert b"Not yours" not in page


def test_designer_inbox_needs_the_designer_role(client, scene, login):
    _, customer, _ = scene
    assert client.get("/designer/enquiries").status_code == 302
    login(customer.username)
    assert client.get("/designer/enquiries").status_code == 403


def test_designer_opens_a_thread_and_replies(client, scene, login):
    designer, customer, idp = scene
    login(customer.username)
    send(client, idp, message="Is it still available?")
    enquiry = EnquiryEntity.query.one()
    client.post("/logout")
    login(designer.username)
    page = client.get(f"/designer/enquiries/{enquiry.enquiryId}").data
    assert b"Is it still available?" in page
    resp = client.post(
        f"/designer/enquiries/{enquiry.enquiryId}", data={"body": "Yes, it is."}
    )
    assert resp.status_code == 302
    assert [m.body for m in enquiry.messages] == ["Is it still available?", "Yes, it is."]
    assert b"Yes, it is." in client.get(f"/designer/enquiries/{enquiry.enquiryId}").data


def test_designer_cannot_open_or_reply_to_another_designers_thread(client, scene, login, make_account):
    _, customer, idp = scene
    login(customer.username)
    send(client, idp)
    enquiry = EnquiryEntity.query.one()
    client.post("/logout")
    login(make_account(role="designer").username)
    assert client.get(f"/designer/enquiries/{enquiry.enquiryId}").status_code == 404
    assert client.post(f"/designer/enquiries/{enquiry.enquiryId}", data={"body": "hi"}).status_code == 404
    assert len(enquiry.messages) == 1


def test_empty_reply_is_not_saved(client, scene, login):
    designer, customer, idp = scene
    login(customer.username)
    send(client, idp)
    enquiry = EnquiryEntity.query.one()
    client.post("/logout")
    login(designer.username)
    client.post(f"/designer/enquiries/{enquiry.enquiryId}", data={"body": "  "})
    assert len(enquiry.messages) == 1


def test_customer_sees_only_their_threads_and_can_reply(client, scene, login, make_account):
    designer, customer, idp = scene
    other = make_account()
    login(other.username)
    send(client, idp, subject="Someone else")
    client.post("/logout")
    login(customer.username)
    send(client, idp, subject="Mine")
    page = client.get("/enquiries").data
    assert b"Mine" in page and b"Someone else" not in page
    mine = EnquiryEntity.query.filter_by(userId=customer.userId).one()
    theirs = EnquiryEntity.query.filter_by(userId=other.userId).one()
    assert client.get(f"/enquiries/{theirs.enquiryId}").status_code == 404
    assert client.post(f"/enquiries/{theirs.enquiryId}", data={"body": "x"}).status_code == 404
    assert client.post(f"/enquiries/{mine.enquiryId}", data={"body": "Follow up"}).status_code == 302
    assert [m.body for m in mine.messages][-1] == "Follow up"


def test_customer_pages_need_the_customer_role(client, scene, login):
    designer, _, _ = scene
    assert client.get("/enquiries").status_code == 302
    login(designer.username)
    assert client.get("/enquiries").status_code == 403


def test_nav_links_follow_the_role(client, scene, login):
    designer, customer, _ = scene
    login(customer.username)
    page = client.get("/").data
    assert b'href="/enquiries"' in page and b"/designer/enquiries" not in page
    client.post("/logout")
    login(designer.username)
    page = client.get("/").data
    assert b'href="/designer/enquiries"' in page
