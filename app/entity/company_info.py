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
