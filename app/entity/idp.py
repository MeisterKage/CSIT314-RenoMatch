from datetime import timedelta

from sqlalchemy import func, or_, select, update

from app.entity.db import db, utcnow
from app.entity.idp_photos import deletePhoto, savePhoto
from app.entity.platform_activity import PlatformActivityEntity
from app.entity.reports import Summary

PAGE_SIZE = 24
RECOMMENDATION_LIMIT = 10
FEATURED_LIMIT = 6
WEEKLY_SUMMARY_DAYS = 7

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

    @classmethod
    def addIDP(cls, idp: dict, photos: list) -> bool:
        """US-38 step 1.1.2: save a new IDP for idp["designerId"], with its photos.

        idp is a dict of the form fields, already validated by the controller. Returns False
        and saves nothing when the category is not Active (6c). Otherwise saves each photo
        under a random name, stores their /uploads/ URLs in photoUrls, records an `idp_added`
        PlatformActivityEntity and returns True.
        """
        from app.entity.category import CategoryEntity

        category = db.session.get(CategoryEntity, int(idp["categoryId"]))
        if category is None or category.status != "Active":
            return False
        urls = [savePhoto(photo) for photo in photos]
        try:
            record = cls(
                designerId=idp["designerId"],
                categoryId=category.categoryId,
                photoUrls=urls,
                **cls._fieldValues(idp),
            )
            db.session.add(record)
            db.session.flush()
            db.session.add(
                PlatformActivityEntity(
                    activityType="idp_added", userId=record.designerId, idpId=record.idpId
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            for url in urls:
                deletePhoto(url)
            raise
        return True

    @staticmethod
    def _fieldValues(idp: dict) -> dict:
        """The column values for the form fields of idp, trimmed and converted."""
        return {
            "title": idp["title"].strip(),
            "description": idp["description"].strip(),
            "style": idp["style"],
            "propertyType": idp["propertyType"],
            "budget": float(idp["budget"]),
            "location": idp["location"].strip(),
            "stage": idp.get("stage") or "Current",
        }

    @classmethod
    def searchMyIDPs(cls, designerId: int, keyword: str | None) -> "list[IDPEntity]":
        """US-42: the designer's IDPs, whatever their status except Removed, newest first.

        keyword matches the title or description, ignoring case. Blank or None lists all.
        """
        query = db.session.query(cls).filter(cls.designerId == designerId, cls.status != "Removed")
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"
            query = query.filter(or_(cls.title.ilike(pattern), cls.description.ilike(pattern)))
        return query.order_by(cls.createdAt.desc(), cls.idpId.desc()).all()

    @classmethod
    def getMyIDP(cls, designerId: int, idpId: int) -> "IDPEntity | None":
        """US-39: the IDP when it belongs to the designer and is not Removed, else None."""
        record = db.session.get(cls, idpId)
        if record is None or record.designerId != designerId or record.status == "Removed":
            return None
        return record

    @classmethod
    def updateIDP(cls, designerId: int, idpId: int, idp: dict, photos: list) -> "bool | None":
        """US-40: change the designer's own IDP. Returns None when it is not theirs.

        idp["removePhotos"] lists photo URLs to drop and photos are new uploads to add. Returns
        False when the category is changed to one that is not Active (6c). Otherwise saves the
        changes, deletes the dropped files and returns True.
        """
        from app.entity.category import CategoryEntity

        record = cls.getMyIDP(designerId, idpId)
        if record is None:
            return None
        category = db.session.get(CategoryEntity, int(idp["categoryId"]))
        if category is None or (
            category.status != "Active" and category.categoryId != record.categoryId
        ):
            return False
        toRemove = set(idp.get("removePhotos") or [])
        dropped = [url for url in record.photoUrls if url in toRemove]
        added = [savePhoto(photo) for photo in photos]
        for name, value in cls._fieldValues(idp).items():
            setattr(record, name, value)
        record.categoryId = category.categoryId
        record.photoUrls = [url for url in record.photoUrls if url not in dropped] + added
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            for url in added:
                deletePhoto(url)
            raise
        for url in dropped:
            deletePhoto(url)
        return True

    @classmethod
    def deleteIDP(cls, designerId: int, idpId: int) -> bool:
        """US-41: mark the designer's own IDP Removed and un-feature it. False if not theirs.

        The row stays so reports and history keep working. A Removed IDP is hidden everywhere.
        """
        record = cls.getMyIDP(designerId, idpId)
        if record is None:
            return False
        record.status = "Removed"
        record.isFeatured = False
        record.featuredDate = None
        db.session.commit()
        return True

    @classmethod
    def getViewCount(cls, idpId: int) -> int:
        """US-43 step 1.1.1: the IDP's viewCount, 0 when it has none or does not exist."""
        record = db.session.get(cls, idpId)
        return record.viewCount if record is not None else 0

    @classmethod
    def getShortlistCount(cls, idpId: int) -> int:
        """US-44: the IDP's shortlistCount, 0 when it has none or does not exist."""
        record = db.session.get(cls, idpId)
        return record.shortlistCount if record is not None else 0

    @classmethod
    def getInterestDashboard(cls, designerId: int) -> dict:
        """US-46: views and shortlists across the designer's IDPs, Removed ones left out.

        byStyle and byCategory are lists of (name, views, shortlists), most views first.
        topIDPs is the 5 IDPs with the most views. maxValue is the largest views or shortlists
        figure shown, which the page uses to size its bars.
        """
        idps = (
            db.session.query(cls)
            .filter(cls.designerId == designerId, cls.status != "Removed")
            .order_by(cls.viewCount.desc(), cls.idpId)
            .all()
        )
        byStyle: dict[str, list[int]] = {}
        byCategory: dict[str, list[int]] = {}
        for idp in idps:
            for totals, name in ((byStyle, idp.style), (byCategory, idp.category.name)):
                pair = totals.setdefault(name, [0, 0])
                pair[0] += idp.viewCount
                pair[1] += idp.shortlistCount

        def ranked(totals):
            rows = [(name, views, shortlists) for name, (views, shortlists) in totals.items()]
            return sorted(rows, key=lambda row: (-row[1], -row[2], row[0]))

        figures = [max(idp.viewCount, idp.shortlistCount) for idp in idps]
        for totals in (byStyle, byCategory):
            figures += [max(pair) for pair in totals.values()]
        return {
            "byStyle": ranked(byStyle),
            "byCategory": ranked(byCategory),
            "topIDPs": idps[:5],
            "maxValue": max(figures, default=0),
        }

    @classmethod
    def getOptedInDesigners(cls) -> "list":
        """US-48 step 1.1.1: the Active designers who have the weekly summary turned on.

        A designer is an account whose profile has the designer role. Suspended accounts and
        accounts on a suspended profile are left out. Ordered by userId.
        """
        from app.entity.user_account import UserAccountEntity
        from app.entity.user_profile import UserProfileEntity

        return (
            db.session.query(UserAccountEntity)
            .join(UserProfileEntity, UserAccountEntity.profileId == UserProfileEntity.profileId)
            .filter(
                UserProfileEntity.roleType == "designer",
                UserProfileEntity.status == "Active",
                UserAccountEntity.status == "Active",
                UserAccountEntity.weeklySummaryOptIn.is_(True),
            )
            .order_by(UserAccountEntity.userId)
            .all()
        )

    @classmethod
    def getWeeklyStats(cls, designerId: int) -> Summary:
        """US-48 step 1.1.2: the designer's views and shortlists of the last 7 days.

        Counts `view` and `shortlist` PlatformActivityEntity rows for the designer's IDPs.
        topIDPs holds up to 3 (title, views) pairs, the most viewed first. IDPs without a
        view that week are not listed.
        """
        from app.entity.user_account import UserAccountEntity

        now = utcnow()
        since = now - timedelta(days=WEEKLY_SUMMARY_DAYS)
        rows = (
            db.session.query(cls.title, PlatformActivityEntity.activityType, func.count())
            .join(PlatformActivityEntity, PlatformActivityEntity.idpId == cls.idpId)
            .filter(
                cls.designerId == designerId,
                PlatformActivityEntity.timestamp >= since,
                PlatformActivityEntity.activityType.in_(("view", "shortlist")),
            )
            .group_by(cls.idpId, cls.title, PlatformActivityEntity.activityType)
            .all()
        )
        views = [(title, count) for title, kind, count in rows if kind == "view"]
        designer = db.session.get(UserAccountEntity, designerId)
        return Summary(
            designerId=designerId,
            startDate=since.date(),
            endDate=now.date(),
            designerName=designer.name if designer is not None else "",
            totalViews=sum(count for _, count in views),
            totalShortlists=sum(count for _, kind, count in rows if kind == "shortlist"),
            topIDPs=sorted(views, key=lambda pair: (-pair[1], pair[0]))[:3],
        )
