"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.category import Category
from app.entity.company_info import CompanyInfo
from app.entity.db import db
from app.entity.idp import IDP
from app.entity.idp_photo import IDPPhoto
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile

__all__ = [
    "IDP",
    "Category",
    "CompanyInfo",
    "IDPPhoto",
    "LoginAttempt",
    "PasswordResetToken",
    "UserAccount",
    "UserProfile",
    "db",
]
