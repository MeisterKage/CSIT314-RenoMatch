"""US-18, US-47: SendEnquiryController, ViewEnquiriesController, ReplyEnquiryController."""

import pytest

from app.control.errors import ValidationError
from app.control.reply_enquiry_controller import ReplyEnquiryController
from app.control.send_enquiry_controller import SendEnquiryController
from app.control.view_enquiries_controller import ViewEnquiriesController


@pytest.fixture
def thread(make_account, make_idp):
    designer = make_account(role="designer")
    customer = make_account()
    idp = make_idp(designer=designer)
    enquiry = SendEnquiryController().sendEnquiry(customer.userId, idp.idpId, "Price", "How much?")
    return designer, customer, idp, enquiry


def test_send_enquiry_creates_thread(thread):
    _, customer, idp, enquiry = thread
    assert enquiry.userId == customer.userId and enquiry.idpId == idp.idpId


@pytest.mark.parametrize(
    "subject,message,field",
    [("", "body", "subject"), ("   ", "body", "subject"), ("s" * 151, "body", "subject"),
     ("s", "", "message"), ("s", "  ", "message"), ("s", "m" * 2001, "message")],
)
def test_send_enquiry_validates_subject_and_message(make_account, make_idp, subject, message, field):
    customer, idp = make_account(), make_idp()
    with pytest.raises(ValidationError) as caught:
        SendEnquiryController().sendEnquiry(customer.userId, idp.idpId, subject, message)
    assert field in caught.value.errors


def test_send_enquiry_to_unavailable_idp_is_none(make_account):
    assert SendEnquiryController().sendEnquiry(make_account().userId, 9999, "s", "m") is None


def test_designer_lists_and_opens_only_their_own_threads(thread, make_account):
    designer, _, _, enquiry = thread
    controller = ViewEnquiriesController()
    assert controller.getEnquiries(designer.userId) == [enquiry]
    assert controller.getEnquiryThread(enquiry.enquiryId, designer.userId) is enquiry
    stranger = make_account(role="designer")
    assert controller.getEnquiries(stranger.userId) == []
    assert controller.getEnquiryThread(enquiry.enquiryId, stranger.userId) is None


def test_customer_lists_and_opens_only_their_own_threads(thread, make_account):
    _, customer, _, enquiry = thread
    controller = ViewEnquiriesController()
    assert controller.getCustomerEnquiries(customer.userId) == [enquiry]
    assert controller.getCustomerEnquiryThread(enquiry.enquiryId, customer.userId) is enquiry
    stranger = make_account()
    assert controller.getCustomerEnquiryThread(enquiry.enquiryId, stranger.userId) is None


def test_designer_reply_is_added(thread):
    designer, _, _, enquiry = thread
    message = ReplyEnquiryController().replyEnquiry(enquiry.enquiryId, designer.userId, "About 40k")
    assert message.senderId == designer.userId and len(enquiry.messages) == 2


def test_reply_by_another_designer_or_empty_body_is_refused(thread, make_account):
    designer, _, _, enquiry = thread
    controller = ReplyEnquiryController()
    stranger = make_account(role="designer")
    assert controller.replyEnquiry(enquiry.enquiryId, stranger.userId, "hi") is None
    with pytest.raises(ValidationError):
        controller.replyEnquiry(enquiry.enquiryId, designer.userId, "   ")
    with pytest.raises(ValidationError):
        controller.replyEnquiry(enquiry.enquiryId, designer.userId, "x" * 2001)
    assert len(enquiry.messages) == 1


def test_customer_reply_goes_through_the_customer_side_method(thread, make_account):
    _, customer, _, enquiry = thread
    controller = ReplyEnquiryController()
    assert controller.replyAsCustomer(enquiry.enquiryId, customer.userId, "Thanks") is not None
    assert controller.replyAsCustomer(enquiry.enquiryId, make_account().userId, "x") is None
    assert len(enquiry.messages) == 2
