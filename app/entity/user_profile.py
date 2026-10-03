from app.entity.db import db

ROLE_TYPES = ("admin", "designer", "customer", "platform")

DEFAULT_PROFILE_NAMES = {
    "admin": "User Admin",
    "designer": "Interior Designer",
    "customer": "Customer",
    "platform": "Platform Manager",
}


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    role_type = db.Column(db.String(20), nullable=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)

    accounts = db.relationship("UserAccount", back_populates="profile")

    @classmethod
    def create(cls, name: str, role_type: str, description: str = "") -> "UserProfile":
        if role_type not in ROLE_TYPES:
            raise ValueError(f"Unknown role type: {role_type}")
        profile = cls(name=name, role_type=role_type, description=description)
        db.session.add(profile)
        db.session.commit()
        return profile

    @classmethod
    def find_by_name(cls, name: str) -> "UserProfile | None":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_default_for_role(cls, role_type: str) -> "UserProfile | None":
        name = DEFAULT_PROFILE_NAMES.get(role_type)
        return cls.find_by_name(name) if name else None
