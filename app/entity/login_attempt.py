from app.entity.db import db, utcnow


class LoginAttemptEntity(db.Model):
    """One login attempt. userId is empty when the username matched no account."""

    __tablename__ = "login_attempt"

    attemptId = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, index=True)
    userId = db.Column("user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    attemptedAt = db.Column(
        "attempted_at", db.DateTime, nullable=False, default=utcnow, index=True
    )

    @classmethod
    def recordAttempt(
        cls, username: str, userId: int | None, success: bool
    ) -> "LoginAttemptEntity":
        attempt = cls(username=username.strip().lower()[:30], userId=userId, success=success)
        db.session.add(attempt)
        db.session.commit()
        return attempt
