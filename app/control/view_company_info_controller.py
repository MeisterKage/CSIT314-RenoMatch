from app.entity import CompanyInfoEntity


class ViewCompanyInfoController:
    """US-36: a designer views their company information."""

    def __init__(self):
        self.entity = CompanyInfoEntity

    def getCompanyInfo(self, designerId):
        return self.entity.findByDesignerId(designerId)
