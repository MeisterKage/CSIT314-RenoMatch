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
