from app.control.company_info_validation import cleanCompanyInfo
from app.entity import CompanyInfoEntity


class UpdateCompanyInfoController:
    """US-37: a designer updates their company information. Returns None when none exists."""

    def __init__(self):
        self.entity = CompanyInfoEntity

    def updateCompanyInfo(self, designerId, name, description, address, phone, email, website):
        values = cleanCompanyInfo(name, description, address, phone, email, website)
        return self.entity.updateCompanyInfo(designerId, **values)
