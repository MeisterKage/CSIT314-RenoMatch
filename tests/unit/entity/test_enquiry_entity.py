"""US-18, US-47: EnquiryEntity."""

from app.entity import EnquiryEntity, EnquiryMessageEntity, IDPEntity, PlatformActivityEntity, db


def test_create_enquiry_stores_thread_first_message_and_activity(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    enquiry = EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "Price?", "What is the cost?")
    assert enquiry.userId == customer.userId
    assert enquiry.designerId == idp.designerId
    assert enquiry.idpId == idp.idpId
    assert enquiry.subject == "Price?"
    (message,) = enquiry.messages
    assert (message.senderId, message.body) == (customer.userId, "What is the cost?")
    activity = PlatformActivityEntity.query.filter_by(activityType="enquiry").one()
    assert (activity.userId, activity.idpId) == (customer.userId, idp.idpId)


def test_create_enquiry_rejects_missing_or_inactive_idp(make_account, make_idp):
    customer = make_account()
    suspended = make_idp(status="Suspended")
    assert EnquiryEntity.createEnquiry(customer.userId, suspended.idpId, "a", "b") is None
    assert EnquiryEntity.createEnquiry(customer.userId, 9999, "a", "b") is None
    assert EnquiryEntity.query.count() == 0
    assert PlatformActivityEntity.query.count() == 0


def test_enquiry_does_not_change_view_or_shortlist_counts(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "a", "b")
    refreshed = db.session.get(IDPEntity, idp.idpId)
    assert (refreshed.viewCount, refreshed.shortlistCount) == (0, 0)


def test_lists_are_scoped_to_the_customer_and_the_designer(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    other_idp = make_idp()
    alice, bob = make_account(), make_account()
    mine = EnquiryEntity.createEnquiry(alice.userId, idp.idpId, "a", "b")
    EnquiryEntity.createEnquiry(bob.userId, other_idp.idpId, "c", "d")
    assert EnquiryEntity.getCustomerEnquiries(alice.userId) == [mine]
    assert EnquiryEntity.getDesignerEnquiries(designer.userId) == [mine]


def test_most_recently_active_thread_comes_first(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    customer = make_account()
    first = EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "first", "one")
    second = EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "second", "two")
    assert EnquiryEntity.getDesignerEnquiries(designer.userId) == [second, first]
    EnquiryEntity.addMessage(first.enquiryId, designer.userId, "reply")
    assert EnquiryEntity.getDesignerEnquiries(designer.userId) == [first, second]


def test_add_message_appends_in_order(make_account, make_idp):
    designer = make_account(role="designer")
    idp = make_idp(designer=designer)
    customer = make_account()
    enquiry = EnquiryEntity.createEnquiry(customer.userId, idp.idpId, "a", "hello")
    message = EnquiryEntity.addMessage(enquiry.enquiryId, designer.userId, "hi there")
    assert isinstance(message, EnquiryMessageEntity)
    assert [m.body for m in EnquiryEntity.getEnquiry(enquiry.enquiryId).messages] == [
        "hello",
        "hi there",
    ]


def test_get_enquiry_unknown_is_none(app):
    assert EnquiryEntity.getEnquiry(9999) is None
