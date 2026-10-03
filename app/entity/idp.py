from app.entity.db import db, utcnow

IDP_STATUSES = ("current", "past")
PROPERTY_TYPES = ("HDB", "Condominium", "Landed", "Commercial")
STYLES = (
    "Modern",
    "Scandinavian",
    "Industrial",
    "Minimalist",
    "Contemporary",
    "Japandi",
    "Luxury",
    "Traditional",
    "Eclectic",
    "Mid-Century",
)


class IDP(db.Model):
    """An interior design project in a designer's portfolio."""

    __tablename__ = "idp"

    id = db.Column(db.Integer, primary_key=True)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    style = db.Column(db.String(30), nullable=False)
    property_type = db.Column(db.String(30), nullable=False)
    budget = db.Column(db.Integer, nullable=False)  # SGD
    location = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="current")
    completed_on = db.Column(db.Date, nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_removed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    designer = db.relationship("UserAccount")
    category = db.relationship("Category")
    photos = db.relationship(
        "IDPPhoto",
        back_populates="idp",
        order_by="IDPPhoto.position",
        cascade="all, delete-orphan",
    )
