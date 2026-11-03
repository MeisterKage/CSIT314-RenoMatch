from app.entity.db import db, utcnow


class CompanyInfoEntity(db.Model):
    """A designer's company details. Each designer has at most one."""

    __tablename__ = "company_info"

    companyId = db.Column("id", db.Integer, primary_key=True)
    designerId = db.Column(
        "designer_id", db.Integer, db.ForeignKey("user_account.id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    phone = db.Column(db.String(20), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    website = db.Column(db.String(200), nullable=False, default="")
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)
    updatedAt = db.Column(
        "updated_at", db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    designer = db.relationship("UserAccountEntity")

    @classmethod
    def findByDesignerId(cls, designerId: int) -> "CompanyInfoEntity | None":
        return db.session.query(cls).filter_by(designerId=designerId).first()

    @classmethod
    def createCompanyInfo(
        cls, designerId, name, description, address, phone, email, website
    ) -> "CompanyInfoEntity":
        company = cls(
            designerId=designerId,
            name=name,
            description=description,
            address=address,
            phone=phone,
            email=email,
            website=website,
        )
        db.session.add(company)
        db.session.commit()
        return company

    @classmethod
    def updateCompanyInfo(
        cls, designerId, name, description, address, phone, email, website
    ) -> "CompanyInfoEntity | None":
        company = cls.findByDesignerId(designerId)
        if company is None:
            return None
        company.name = name
        company.description = description
        company.address = address
        company.phone = phone
        company.email = email
        company.website = website
        db.session.commit()
        return company
