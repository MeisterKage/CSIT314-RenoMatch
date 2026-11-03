import hashlib
import secrets
import threading
from datetime import timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from app.entity.db import db, utcnow

ACCOUNT_STATUSES = ("Active", "Suspended")
RESET_TOKEN_LIFETIME = timedelta(hours=1)
DELETED_NAME = "Deleted user"

# The raw reset token exists only until the link is emailed (the database keeps its hash).
# It is handed to the controller's private sendResetLink through takeIssuedResetToken.
_issued = threading.local()


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

    def setPassword(self, password: str) -> None:
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password: str) -> bool:
        return check_password_hash(self.passwordHash, password)

    def changePassword(self, newPassword: str) -> None:
        self.setPassword(newPassword)
        db.session.commit()

    @classmethod
    def requestPasswordReset(cls, email: str) -> bool:
        """US-05 1.1.1: for an active account with this email, store a hashed single-use
        token that expires in 1 hour and return True (emailFound). Otherwise False."""
        account = cls.findByEmail(email.strip())
        if account is None or not account.canLogIn():
            return False
        token = secrets.token_urlsafe(32)
        account.resetToken = hashToken(token)
        account.tokenExpiry = utcnow() + RESET_TOKEN_LIFETIME
        db.session.commit()
        if not hasattr(_issued, "tokens"):
            _issued.tokens = {}
        _issued.tokens[account.email] = token
        return True

    @classmethod
    def takeIssuedResetToken(cls, email: str) -> str | None:
        """The raw token just issued for this email, once. Used by sendResetLink."""
        return getattr(_issued, "tokens", {}).pop(email.strip().lower(), None)

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
        db.session.commit()

    def canLogIn(self) -> bool:
        return (
            self.status == "Active"
            and not self.isAnonymised
            and self.profile.status == "Active"
        )
