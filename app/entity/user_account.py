from werkzeug.security import check_password_hash, generate_password_hash

from app.entity.db import db, utcnow

ACCOUNT_STATUSES = ("Active", "Suspended")


class UserAccountEntity(db.Model):
    """A registered user. Usernames and emails are stored lowercase."""

    __tablename__ = "user_account"

    userId = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False, default="")
    passwordHash = db.Column("password_hash", db.String(255), nullable=False)
    profileId = db.Column(
        "profile_id", db.Integer, db.ForeignKey("user_profile.id"), nullable=False
    )
    status = db.Column(db.String(10), nullable=False, default="Active")
    failedLogins = db.Column("failed_logins", db.Integer, nullable=False, default=0)
    lockedUntil = db.Column("locked_until", db.DateTime, nullable=True)
    resetToken = db.Column("reset_token", db.String(255), unique=True, nullable=True)  # hashed
    tokenExpiry = db.Column("token_expiry", db.DateTime, nullable=True)
    weeklySummaryOptIn = db.Column(
        "weekly_summary_opt_in", db.Boolean, nullable=False, default=True
    )
    isAnonymised = db.Column("is_anonymised", db.Boolean, nullable=False, default=False)
    createdAt = db.Column("created_at", db.DateTime, nullable=False, default=utcnow)

    profile = db.relationship("UserProfileEntity", back_populates="accounts")

    @property
    def role(self) -> str:
        return self.profile.roleType

    @classmethod
    def createUserAccount(
        cls, username, email, password, name, profile, phone=""
    ) -> "UserAccountEntity":
        account = cls(
            username=username.lower(),
            email=email.lower(),
            name=name,
            phone=phone,
            profile=profile,
        )
        account.setPassword(password)
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def findById(cls, userId: int) -> "UserAccountEntity | None":
        return db.session.get(cls, userId)

    @classmethod
    def findByUsername(cls, username: str) -> "UserAccountEntity | None":
        return cls.query.filter_by(username=username.lower()).first()

    @classmethod
    def findByEmail(cls, email: str) -> "UserAccountEntity | None":
        return cls.query.filter_by(email=email.lower()).first()

    def setPassword(self, password: str) -> None:
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password: str) -> bool:
        return check_password_hash(self.passwordHash, password)

    def changePassword(self, newPassword: str) -> None:
        self.setPassword(newPassword)
        db.session.commit()

    def canLogIn(self) -> bool:
        return (
            self.status == "Active"
            and not self.isAnonymised
            and self.profile.status == "Active"
        )
