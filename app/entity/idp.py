from app.entity.db import db, utcnow

IDP_STATUSES = ("Active", "Suspended", "Removed")
IDP_STAGES = ("Current", "Past")
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


class IDPEntity(db.Model):
    """An interior design project (IDP) in a designer's portfolio.

    photoUrls is a JSON list of image URLs. viewCount and shortlistCount are stored
    counters that match the IDP's view and shortlist PlatformActivityEntity rows.
    """

    __tablename__ = "idp"

    idpId = db.Column("id", db.Integer, primary_key=True)
    designerId = db.Column(
        "designer_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    categoryId = db.Column(
        "category_id", db.Integer, db.ForeignKey("category.id"), nullable=False, index=True
    )
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    style = db.Column(db.String(30), nullable=False)
    propertyType = db.Column("property_type", db.String(30), nullable=False)
    budget = db.Column(db.Float, nullable=False)  # SGD
    location = db.Column(db.String(60), nullable=False)
    photoUrls = db.Column("photo_urls", db.JSON, nullable=False, default=list)
    stage = db.Column(db.String(10), nullable=False, default="Current")
    status = db.Column(db.String(10), nullable=False, default="Active", index=True)
    isFeatured = db.Column("is_featured", db.Boolean, nullable=False, default=False)
    featuredDate = db.Column("featured_date", db.Date, nullable=True)
    viewCount = db.Column("view_count", db.Integer, nullable=False, default=0)
    shortlistCount = db.Column("shortlist_count", db.Integer, nullable=False, default=0)
    completedOn = db.Column("completed_on", db.Date, nullable=True)
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)

    designer = db.relationship("UserAccountEntity")
    category = db.relationship("CategoryEntity")
