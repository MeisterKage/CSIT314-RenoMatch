from sqlalchemy import or_, select, update

from app.entity.db import db, utcnow
from app.entity.platform_activity import PlatformActivityEntity

PAGE_SIZE = 24

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

    @classmethod
    def getActiveIDPs(cls, page: int = 1, perPage: int = PAGE_SIZE):
        """US-01: one page of Active IDPs, newest first."""
        return cls.searchIDPs(None, None, None, None, None, None, page, perPage)

    @classmethod
    def searchIDPs(
        cls,
        keyword,
        categoryId,
        style,
        propertyType,
        minBudget,
        maxBudget,
        page: int = 1,
        perPage: int = PAGE_SIZE,
    ):
        """US-09: one page of Active IDPs matching every filter that is given.

        keyword matches the title or description, ignoring case. Blank or None filters
        are skipped. The budget range includes both ends.
        """
        query = select(cls).where(cls.status == "Active")
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"
            query = query.where(or_(cls.title.ilike(pattern), cls.description.ilike(pattern)))
        if categoryId is not None:
            query = query.where(cls.categoryId == categoryId)
        if style:
            query = query.where(cls.style == style)
        if propertyType:
            query = query.where(cls.propertyType == propertyType)
        if minBudget is not None:
            query = query.where(cls.budget >= minBudget)
        if maxBudget is not None:
            query = query.where(cls.budget <= maxBudget)
        query = query.order_by(cls.createdAt.desc(), cls.idpId.desc())
        return db.paginate(query, page=page, per_page=perPage, error_out=False)

    @classmethod
    def recordView(cls, idpId: int, viewerId: int | None) -> "IDPEntity | None":
        """US-10: return the Active IDP and count the view, unless the viewer owns it.

        Adds a `view` PlatformActivityEntity and increments viewCount together. Returns
        None when the IDP does not exist or is not Active, and records nothing.
        """
        idp = db.session.get(cls, idpId)
        if idp is None or idp.status != "Active":
            return None
        if viewerId != idp.designerId:
            db.session.add(
                PlatformActivityEntity(activityType="view", userId=viewerId, idpId=idpId)
            )
            db.session.execute(
                update(cls).where(cls.idpId == idpId).values(viewCount=cls.viewCount + 1)
            )
            db.session.commit()
            db.session.refresh(idp)
        return idp

    @classmethod
    def getActiveByDesigner(cls, designerId: int) -> "list[IDPEntity]":
        """US-11: a designer's Active IDPs, newest first."""
        return (
            db.session.query(cls)
            .filter_by(designerId=designerId, status="Active")
            .order_by(cls.createdAt.desc(), cls.idpId.desc())
            .all()
        )
