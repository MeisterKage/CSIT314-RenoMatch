from app.control.company_info_validation import cleanCompanyInfo
from app.control.errors import ValidationError
from app.entity import CompanyInfoEntity


class CreateCompanyInfoController:
    """US-35: a designer creates their company information. One record per designer."""

    def __init__(self):
        self.entity = CompanyInfoEntity

    def createCompanyInfo(self, designerId, name, description, address, phone, email, website):
        values = cleanCompanyInfo(name, description, address, phone, email, website)
        if self.entity.findByDesignerId(designerId) is not None:
            raise ValidationError({"name": "Your company information already exists."})
        return self.entity.createCompanyInfo(designerId, **values)
