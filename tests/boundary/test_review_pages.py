"""US-19: the Write a Review flow on DesignerProfilePage, branch by branch."""

import pytest

from app.boundary.browse import DesignerProfilePage
from app.control.rate_review_designer_controller import RateReviewDesignerController
from app.entity import EnquiryEntity, ReviewEntity

NOT_CONTACTED = "You can only review designers you have contacted"
INVALID = "Select a rating and keep your comment within 1,000 characters"


@pytest.fixture
def scene(make_account, make_idp):
    designer = make_account(role="designer")
    customer = make_account()
    idp = make_idp(designer=designer)
    return designer, customer, idp


def contact(customer, idp):
    EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "Hi", "Is it available?")


def url(designer):
    return f"/designers/{designer.userId}/review"


def test_profile_shows_write_a_review_link_to_customers_only(client, scene, login):
    designer, customer, _ = scene
    assert url(designer).encode() not in client.get(f"/designers/{designer.userId}").data
    login(customer.username)
    assert url(designer).encode() in client.get(f"/designers/{designer.userId}").data


def test_review_page_needs_a_customer(client, scene, make_account, login):
    designer, _, _ = scene
    assert client.get(url(designer)).status_code == 302
    login(make_account(role="designer").username)
    assert client.get(url(designer)).status_code == 403
    assert client.post(url(designer), data={"rating": "5"}).status_code == 403


def test_eligible_user_gets_an_empty_form(client, scene, login):
    designer, customer, idp = scene
    contact(customer, idp)
    login(customer.username)
    page = client.get(url(designer)).data
    assert b'name="rating"' in page
    assert b'name="comment"' in page
    assert NOT_CONTACTED.encode() not in page


def test_never_contacted_sees_the_message_and_no_form(client, scene, login):
    designer, customer, _ = scene
    login(customer.username)
    page = client.get(url(designer)).data
    assert NOT_CONTACTED.encode() in page
    assert b'name="rating"' not in page


def test_already_reviewed_gets_the_form_filled_with_the_existing_review(client, scene, login):
    designer, customer, idp = scene
    contact(customer, idp)
    ReviewEntity.submitReview(designer.userId, customer.userId, 4, "Solid work")
    login(customer.username)
    page = client.get(url(designer)).data
    assert b"Solid work" in page
    assert b'value="4" checked' in page


def test_valid_submission_saves_and_shows_the_review_and_new_average(client, scene, login):
    designer, customer, idp = scene
    contact(customer, idp)
    login(customer.username)
    resp = client.post(url(designer), data={"rating": "4", "comment": "Great job"})
    assert resp.status_code == 302
    page = client.get(resp.headers["Location"]).data
    assert b"Great job" in page
    assert b"4.0" in page
    assert ReviewEntity.getAverageRating(designer.userId) == 4.0


def test_resubmitting_replaces_the_review_and_updates_the_average(client, scene, login):
    designer, customer, idp = scene
    contact(customer, idp)
    login(customer.username)
    client.post(url(designer), data={"rating": "2", "comment": "First"})
    client.post(url(designer), data={"rating": "5", "comment": "Second"})
    assert ReviewEntity.query.count() == 1
    assert ReviewEntity.getAverageRating(designer.userId) == 5.0


@pytest.mark.parametrize(
    "data",
    [
        {"comment": "No rating"},
        {"rating": "7", "comment": "x"},
        {"rating": "abc"},
        {"rating": "3", "comment": "x" * 1001},
    ],
)
def test_invalid_submission_shows_a_message_and_stores_nothing(client, scene, login, data):
    designer, customer, idp = scene
    contact(customer, idp)
    login(customer.username)
    resp = client.post(url(designer), data=data, follow_redirects=True)
    assert INVALID.encode() in resp.data
    assert ReviewEntity.query.count() == 0


def test_submission_without_contact_is_refused(client, scene, login):
    designer, customer, _ = scene
    login(customer.username)
    client.post(url(designer), data={"rating": "5", "comment": "Hi"}, follow_redirects=True)
    assert ReviewEntity.query.count() == 0


def test_unknown_designer_is_404(client, scene, login):
    _, customer, _ = scene
    login(customer.username)
    assert client.get("/designers/9999/review").status_code == 404


def record(monkeypatch):
    calls = []

    def wrap(cls, name):
        original = getattr(cls, name)

        def wrapper(self, *args, **kwargs):
            calls.append(name)
            return original(self, *args, **kwargs)

        monkeypatch.setattr(cls, name, wrapper)

    for name in ("checkEligibility", "submitReview"):
        wrap(RateReviewDesignerController, name)
    for name in ("displayReviewForm", "displayReview", "displayMessage"):
        wrap(DesignerProfilePage, name)
    return calls


def test_sequence_for_each_alt_branch(client, scene, login, monkeypatch):
    designer, customer, idp = scene
    calls = record(monkeypatch)
    login(customer.username)

    client.get(url(designer))  # 1.1 then 1.3
    assert calls == ["checkEligibility", "displayMessage"]

    calls.clear()
    contact(customer, idp)
    client.get(url(designer))  # 1.1 then 1.2
    assert calls == ["checkEligibility", "displayReviewForm"]

    calls.clear()
    client.post(url(designer), data={"rating": "9"})  # 2.1 then 2.3
    assert calls == ["submitReview", "displayMessage"]

    calls.clear()
    client.post(url(designer), data={"rating": "5", "comment": "ok"})  # 2.1 then 2.2
    assert calls == ["submitReview", "displayReview"]

    calls.clear()
    client.get(url(designer))  # 1.1 then 1.4
    assert calls == ["checkEligibility", "displayReviewForm"]
