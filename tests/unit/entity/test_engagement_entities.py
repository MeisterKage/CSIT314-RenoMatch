from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import (
    AuditLogEntity,
    EnquiryEntity,
    EnquiryMessageEntity,
    FavouriteEntity,
    ReviewEntity,
    db,
)
from app.entity.db import utcnow


def test_user_can_favourite_an_idp_only_once(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    db.session.add(FavouriteEntity(user=customer, idp=idp, note="Nice kitchen"))
    db.session.commit()
    db.session.add(FavouriteEntity(user=customer, idp=idp))
    with pytest.raises(IntegrityError):
        db.session.commit()


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_must_be_between_1_and_5(make_account, rating):
    customer, designer = make_account(), make_account(role="designer")
    db.session.add(ReviewEntity(user=customer, designer=designer, rating=rating))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_enquiry_messages_are_ordered_by_time(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    enquiry = EnquiryEntity(user=customer, designer=idp.designer, idp=idp, subject="Price?")
    now = utcnow()
    enquiry.messages.append(
        EnquiryMessageEntity(sender=idp.designer, body="Reply", sentAt=now + timedelta(hours=1))
    )
    enquiry.messages.append(EnquiryMessageEntity(sender=customer, body="Question", sentAt=now))
    db.session.add(enquiry)
    db.session.commit()
    db.session.expire_all()
    reloaded = db.session.get(EnquiryEntity, enquiry.enquiryId)
    assert [m.body for m in reloaded.messages] == ["Question", "Reply"]


def test_audit_log_records_admin_and_target(make_account):
    admin, target = make_account(role="admin"), make_account()
    entry = AuditLogEntity(
        admin=admin, action="suspend_account", targetType="user_account", targetId=target.userId
    )
    db.session.add(entry)
    db.session.commit()
    assert entry.timestamp is not None
    assert entry.admin.role == "admin"
