from sqlalchemy import func

from app.entity.db import db
from app.entity.idp import IDPEntity

CATEGORY_STATUSES = ("Active", "Suspended")


class CategoryEntity(db.Model):
    """An IDP category managed by the platform manager."""

    __tablename__ = "category"

    categoryId = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    status = db.Column(db.String(10), nullable=False, default="Active")

    @property
    def idpCount(self) -> int:
        """Read-only: the number of Active IDPs in this category."""
        return (
            db.session.query(IDPEntity)
            .filter_by(categoryId=self.categoryId, status="Active")
            .count()
        )

    @classmethod
    def getActiveCategories(cls) -> "list[CategoryEntity]":
        """Active categories by name, for the browse filter."""
        return db.session.query(cls).filter_by(status="Active").order_by(cls.name).all()

    @classmethod
    def searchCategories(cls, keyword: str, status: str) -> "list[CategoryEntity]":
        """US-54: categories whose name contains keyword (ignoring case, with % and _ taken
        literally), limited to one status when `status` is Active or Suspended. Any other
        status, such as "" or "all", means no filter. Ordered by name."""
        query = db.session.query(cls)
        keyword = (keyword or "").strip().lower()
        if keyword:
            query = query.filter(func.lower(cls.name).contains(keyword, autoescape=True))
        if status in CATEGORY_STATUSES:
            query = query.filter(cls.status == status)
        return query.order_by(func.lower(cls.name)).all()

    @classmethod
    def createCategory(cls, name: str, description: str = "") -> "CategoryEntity":
        category = cls(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        return category

    @classmethod
    def findById(cls, categoryId: int) -> "CategoryEntity | None":
        return db.session.get(cls, categoryId)

    @classmethod
    def nameTaken(cls, name: str, exceptCategoryId: int | None = None) -> bool:
        """True if another category already uses this name (ignoring case)."""
        query = db.session.query(cls).filter(func.lower(cls.name) == name.strip().lower())
        if exceptCategoryId is not None:
            query = query.filter(cls.categoryId != exceptCategoryId)
        return query.first() is not None

    def updateCategory(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        db.session.commit()

    def suspend(self) -> None:
        self.status = "Suspended"
        db.session.commit()

    def reactivate(self) -> None:
        self.status = "Active"
        db.session.commit()
