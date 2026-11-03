from sqlalchemy import func, or_

from app.entity.db import db

ROLE_TYPES = ("admin", "designer", "customer", "platform")
PROFILE_STATUSES = ("Active", "Suspended")

DEFAULT_PROFILE_NAMES = {
    "admin": "User Admin",
    "designer": "Interior Designer",
    "customer": "Customer",
    "platform": "Platform Manager",
}


class UserProfileEntity(db.Model):
    """A user profile: a named group of accounts that share one role type."""

    __tablename__ = "user_profile"

    profileId = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    roleType = db.Column("role_type", db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="Active")

    accounts = db.relationship("UserAccountEntity", back_populates="profile")

    @classmethod
    def createUserProfile(
        cls, name: str, roleType: str, description: str = ""
    ) -> "UserProfileEntity":
        if roleType not in ROLE_TYPES:
            raise ValueError(f"Unknown role type: {roleType}")
        profile = cls(name=name, roleType=roleType, description=description)
        db.session.add(profile)
        db.session.commit()
        return profile

    @property
    def accountCount(self) -> int:
        """US-27: how many accounts have this profile."""
        return len(self.accounts)

    @classmethod
    def searchUserProfiles(cls, keyword: str, role: str, status: str) -> list["UserProfileEntity"]:
        """US-31: profiles whose name or description contains keyword (ignoring case),
        optionally limited to one role type and one status. An empty value means no
        filter. Ordered by profileId."""
        query = cls.query
        keyword = (keyword or "").strip().lower()
        if keyword:
            query = query.filter(
                or_(
                    func.lower(cls.name).contains(keyword, autoescape=True),
                    func.lower(cls.description).contains(keyword, autoescape=True),
                )
            )
        if role:
            query = query.filter(cls.roleType == role)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.profileId).all()

    @classmethod
    def nameTaken(cls, name: str, exceptProfileId: int | None = None) -> bool:
        """True if another profile already uses this name (ignoring case)."""
        query = cls.query.filter(func.lower(cls.name) == name.strip().lower())
        if exceptProfileId is not None:
            query = query.filter(cls.profileId != exceptProfileId)
        return query.first() is not None

    def updateUserProfile(self, name: str, description: str) -> None:
        """US-28: the role type is fixed once the profile exists."""
        self.name = name
        self.description = description
        db.session.commit()

    def suspend(self) -> None:
        self.status = "Suspended"
        db.session.commit()

    def reactivate(self) -> None:
        self.status = "Active"
        db.session.commit()

    @classmethod
    def findById(cls, profileId: int) -> "UserProfileEntity | None":
        return db.session.get(cls, profileId)

    @classmethod
    def findAll(cls) -> list["UserProfileEntity"]:
        return cls.query.order_by(cls.profileId).all()

    @classmethod
    def findByName(cls, name: str) -> "UserProfileEntity | None":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def findDefaultForRole(cls, roleType: str) -> "UserProfileEntity | None":
        name = DEFAULT_PROFILE_NAMES.get(roleType)
        return cls.findByName(name) if name else None
