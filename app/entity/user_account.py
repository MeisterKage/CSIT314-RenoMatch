from werkzeug.security import check_password_hash, generate_password_hash

from app.entity.db import db, utcnow


class UserAccount(db.Model):
    __tablename__ = "user_account"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, default="")
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    is_anonymised = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    profile = db.relationship("UserProfile", back_populates="accounts")

    @property
    def role(self) -> str:
        return self.profile.role_type

    @classmethod
    def create(cls, username, email, password, full_name, profile, phone="") -> "UserAccount":
        account = cls(
            username=username,
            email=email.lower(),
            full_name=full_name,
            phone=phone,
            profile=profile,
        )
        account.set_password(password)
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def find_by_id(cls, account_id: int) -> "UserAccount | None":
        return db.session.get(cls, account_id)

    @classmethod
    def find_by_username(cls, username: str) -> "UserAccount | None":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email: str) -> "UserAccount | None":
        return cls.query.filter_by(email=email.lower()).first()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def change_password(self, new_password: str) -> None:
        self.set_password(new_password)
        db.session.commit()

    def can_log_in(self) -> bool:
        return not (self.is_suspended or self.is_anonymised or self.profile.is_suspended)
