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

    @classmethod
    def findByName(cls, name: str) -> "UserProfileEntity | None":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def findDefaultForRole(cls, roleType: str) -> "UserProfileEntity | None":
        name = DEFAULT_PROFILE_NAMES.get(roleType)
        return cls.findByName(name) if name else None
