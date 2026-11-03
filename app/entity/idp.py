from sqlalchemy import or_, select, update

from app.entity.db import db, utcnow
from app.entity.platform_activity import PlatformActivityEntity

PAGE_SIZE = 24
RECOMMENDATION_LIMIT = 10
FEATURED_LIMIT = 6

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

    @classmethod
    def compareIDPs(cls, idpIds: "list[int]") -> "list[IDPEntity]":
        """US-13 step 2.1.1: the Active IDPs among idpIds, in the order given.

        Missing, Suspended and Removed IDPs are left out (alt 3a).
        """
        found = {
            idp.idpId: idp
            for idp in db.session.query(cls).filter(cls.idpId.in_(idpIds), cls.status == "Active")
        }
        return [found[idpId] for idpId in idpIds if idpId in found]

    @classmethod
    def getPopularIDPs(cls) -> "list[IDPEntity]":
        """US-12 step 1.1.2: the top 10 Active IDPs by viewCount."""
        return (
            db.session.query(cls)
            .filter_by(status="Active")
            .order_by(cls.viewCount.desc(), cls.idpId.desc())
            .limit(RECOMMENDATION_LIMIT)
            .all()
        )

    @classmethod
    def getFeaturedIDPs(cls) -> "list[IDPEntity]":
        """US-60 home page: the 6 most recently featured Active IDPs."""
        return (
            db.session.query(cls)
            .filter_by(status="Active", isFeatured=True)
            .order_by(cls.featuredDate.desc(), cls.idpId.desc())
            .limit(FEATURED_LIMIT)
            .all()
        )

    @classmethod
    def getRecommendedIDPs(cls, userId: int) -> "list[IDPEntity] | None":
        """US-12 step 1.1.1: up to 10 Active IDPs like the ones the user viewed or saved.

        Returns [] when the user has no viewing or saving history (alt 2a) and None when
        there is history but nothing matches (alt 3a). An IDP matches by sharing a category
        or a style with one in the history. Ranked by number of matches, then viewCount.
        Saved IDPs are excluded.
        """
        from app.entity.favourite import FavouriteEntity

        viewedIds = {
            row[0]
            for row in db.session.query(PlatformActivityEntity.idpId).filter(
                PlatformActivityEntity.userId == userId,
                PlatformActivityEntity.activityType == "view",
                PlatformActivityEntity.idpId.isnot(None),
            )
        }
        savedIds = {
            row[0]
            for row in db.session.query(FavouriteEntity.idpId).filter_by(userId=userId)
        }
        history = db.session.query(cls).filter(cls.idpId.in_(viewedIds | savedIds)).all()
        if not history:
            return []
        categoryIds = {idp.categoryId for idp in history}
        styles = {idp.style for idp in history}
        candidates = db.session.query(cls).filter(
            cls.status == "Active", cls.idpId.notin_(savedIds)
        )
        scored = [
            ((idp.categoryId in categoryIds) + (idp.style in styles), idp)
            for idp in candidates
        ]
        matches = [pair for pair in scored if pair[0] > 0]
        if not matches:
            return None
        matches.sort(key=lambda pair: (-pair[0], -pair[1].viewCount, -pair[1].idpId))
        return [idp for _, idp in matches[:RECOMMENDATION_LIMIT]]
