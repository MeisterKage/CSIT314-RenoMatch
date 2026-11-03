from app.entity import EnquiryEntity


class ViewEnquiriesController:
    """US-47: a designer's enquiry inbox and threads. The customer side lists their own."""

    def __init__(self):
        self.entity = EnquiryEntity

    def getEnquiries(self, designerId: int):
        return self.entity.getDesignerEnquiries(designerId)

    def getEnquiryThread(self, enquiryId: int, designerId: int):
        """The thread, or None when it does not exist or is addressed to another designer."""
        enquiry = self.entity.getEnquiry(enquiryId)
        if enquiry is None or enquiry.designerId != designerId:
            return None
        return enquiry

    def getCustomerEnquiries(self, userId: int):
        return self.entity.getCustomerEnquiries(userId)

    def getCustomerEnquiryThread(self, enquiryId: int, userId: int):
        """The thread, or None when it does not exist or belongs to another customer."""
        enquiry = self.entity.getEnquiry(enquiryId)
        if enquiry is None or enquiry.userId != userId:
            return None
        return enquiry
