from app.entity.db import db, utcnow


class LoginAttempt(db.Model):
    __tablename__ = "login_attempt"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
