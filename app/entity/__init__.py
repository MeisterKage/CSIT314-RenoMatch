"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.db import db
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile

__all__ = ["LoginAttempt", "PasswordResetToken", "UserAccount", "UserProfile", "db"]
