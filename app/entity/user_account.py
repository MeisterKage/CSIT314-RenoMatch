import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from app.entity.db import db, utcnow
from app.entity.user_profile import UserProfileEntity

ACCOUNT_STATUSES = ("Active", "Suspended")
RESET_TOKEN_LIFETIME = timedelta(hours=1)
DELETED_NAME = "Deleted user"
MAX_FAILED_LOGINS = 5
LOCK_DURATION = timedelta(minutes=15)


def hashToken(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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

    @classmethod
    def searchUserAccounts(
        cls, keyword: str, profile: str, status: str
    ) -> list["UserAccountEntity"]:
        """US-25 and US-34: accounts whose username, name or email contains keyword (ignoring
        case), optionally limited to one profile and one status. `profile` is the profile
        NAME (for example "Customer"), `status` is "Active" or "Suspended". An empty value
        means no filter. Ordered by userId."""
        query = cls.query
        keyword = (keyword or "").strip().lower()
        if keyword:
            query = query.filter(
                or_(
                    func.lower(cls.username).contains(keyword, autoescape=True),
                    func.lower(cls.name).contains(keyword, autoescape=True),
                    func.lower(cls.email).contains(keyword, autoescape=True),
                )
            )
        if profile:
            query = query.join(cls.profile).filter(UserProfileEntity.name == profile)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.userId).all()

    def setPassword(self, password: str) -> None:
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password: str) -> bool:
        return check_password_hash(self.passwordHash, password)

    def changePassword(self, newPassword: str) -> None:
        self.setPassword(newPassword)
        db.session.commit()

    @classmethod
    def requestPasswordReset(cls, email: str) -> str | None:
        """Returns the raw reset token if the email is registered (truthy = emailFound in the
        US-05 sequence diagram), else None. The database keeps only the token's hash, which
        expires in 1 hour."""
        account = cls.findByEmail(email.strip())
        if account is None or not account.canLogIn():
            return None
        token = secrets.token_urlsafe(32)
        account.resetToken = hashToken(token)
        account.tokenExpiry = utcnow() + RESET_TOKEN_LIFETIME
        db.session.commit()
        return token

    @classmethod
    def resetPassword(cls, token: str, newPassword: str) -> bool:
        """US-05 2.1.2: set the new password if the token matches and has not expired, then
        discard the token so it cannot be used again."""
        account = cls.query.filter_by(resetToken=hashToken(token)).first()
        if account is None or account.tokenExpiry is None or account.tokenExpiry < utcnow():
            return False
        account.setPassword(newPassword)
        account.resetToken = None
        account.tokenExpiry = None
        db.session.commit()
        return True

    def updateDetails(self, name: str, email: str, phone: str) -> None:
        self.name = name
        self.email = email.lower()
        self.phone = phone
        db.session.commit()

    def setWeeklySummaryOptIn(self, optIn: bool) -> None:
        self.weeklySummaryOptIn = optIn
        db.session.commit()

    def anonymise(self) -> None:
        """US-08: replace the personal details. The row stays so reviews and enquiries keep
        their links and show "Deleted user"."""
        self.name = DELETED_NAME
        self.username = f"deleted{self.userId}"
        self.email = f"deleted{self.userId}@deleted.invalid"
        self.phone = ""
        self.resetToken = None
        self.tokenExpiry = None
        self.isAnonymised = True
        if self.role == "designer":
            from app.entity.idp import IDPEntity

            for idp in IDPEntity.query.filter_by(designerId=self.userId):
                idp.status = "Removed"
                idp.isFeatured = False
        db.session.commit()

    def canLogIn(self) -> bool:
        return (
            self.status == "Active"
            and not self.isAnonymised
            and self.profile.status == "Active"
        )

    def isLocked(self) -> bool:
        """True while lockedUntil is in the future."""
        return self.lockedUntil is not None and self.lockedUntil > utcnow()

    def registerFailedLogin(self) -> None:
        """Count a failed login. The fifth in a row locks the account for 15 minutes. A lock
        that has run out is cleared first, so the count starts again from zero."""
        if self.lockedUntil is not None and not self.isLocked():
            self.lockedUntil = None
            self.failedLogins = 0
        self.failedLogins += 1
        if self.failedLogins >= MAX_FAILED_LOGINS:
            self.lockedUntil = utcnow() + LOCK_DURATION
        db.session.commit()

    def resetFailedLogins(self) -> None:
        """A successful login clears the count and any expired lock."""
        self.failedLogins = 0
        self.lockedUntil = None
        db.session.commit()

    def updateUserAccount(self, name: str, email: str, phone: str, profile) -> None:
        """US-22: an administrator changes the details and the profile."""
        self.name = name
        self.email = email.lower()
        self.phone = phone
        self.profile = profile
        db.session.commit()

    def suspend(self) -> None:
        self.status = "Suspended"
        db.session.commit()

    def reactivate(self) -> None:
        self.status = "Active"
        db.session.commit()

    def unlock(self) -> None:
        """US-33: clear the lock and the failed login count."""
        self.failedLogins = 0
        self.lockedUntil = None
        db.session.commit()
