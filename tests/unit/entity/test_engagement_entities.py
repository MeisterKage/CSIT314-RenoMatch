from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import (
    AuditLog,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    Review,
    ShortlistEvent,
    ViewEvent,
    db,
)
from app.entity.db import utcnow


def test_customer_can_favourite_an_idp_only_once(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    db.session.add(Favourite(customer=customer, idp=idp, note="Nice kitchen"))
    db.session.commit()
    db.session.add(Favourite(customer=customer, idp=idp))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_view_event_allows_anonymous_visitor(make_idp):
    event = ViewEvent(idp_id=make_idp().id, viewer_id=None)
    db.session.add(event)
    db.session.commit()
    assert event.viewed_at is not None


def test_shortlist_events_accumulate_independently_of_favourites(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    db.session.add_all(
        [ShortlistEvent(idp_id=idp.id, customer_id=customer.id) for _ in range(2)]
    )
    db.session.commit()
    assert db.session.query(ShortlistEvent).filter_by(idp_id=idp.id).count() == 2


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_must_be_between_1_and_5(make_account, rating):
    customer, designer = make_account(), make_account(role="designer")
    db.session.add(Review(customer=customer, designer=designer, rating=rating))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_enquiry_messages_are_ordered_by_time(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    enquiry = Enquiry(customer=customer, designer=idp.designer, idp=idp, subject="Price?")
    now = utcnow()
    enquiry.messages.append(
        EnquiryMessage(sender=idp.designer, body="Reply", sent_at=now + timedelta(hours=1))
    )
    enquiry.messages.append(EnquiryMessage(sender=customer, body="Question", sent_at=now))
    db.session.add(enquiry)
    db.session.commit()
    db.session.expire_all()
    assert [m.body for m in db.session.get(Enquiry, enquiry.id).messages] == ["Question", "Reply"]


def test_new_flag_is_open_and_unreviewed(make_account, make_idp):
    flag = IDPFlag(idp=make_idp(), reporter=make_account(), reason="Copied photos")
    db.session.add(flag)
    db.session.commit()
    assert flag.status == "open"
    assert flag.reviewed_by is None
    assert flag.created_at is not None


def test_audit_log_records_actor_and_target(make_account):
    admin, target = make_account(role="admin"), make_account()
    entry = AuditLog(
        actor=admin, action="suspend_account", target_type="user_account", target_id=target.id
    )
    db.session.add(entry)
    db.session.commit()
    assert entry.created_at is not None
    assert entry.actor.role == "admin"
