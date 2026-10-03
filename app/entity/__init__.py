"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.audit_log import AuditLog
from app.entity.category import Category
from app.entity.company_info import CompanyInfo
from app.entity.db import db
from app.entity.enquiry import Enquiry, EnquiryMessage
from app.entity.favourite import Favourite
from app.entity.idp import IDP
from app.entity.idp_flag import IDPFlag
from app.entity.idp_photo import IDPPhoto
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.review import Review
from app.entity.shortlist_event import ShortlistEvent
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile
from app.entity.view_event import ViewEvent

__all__ = [
    "IDP",
    "AuditLog",
    "Category",
    "CompanyInfo",
    "Enquiry",
    "EnquiryMessage",
    "Favourite",
    "IDPFlag",
    "IDPPhoto",
    "LoginAttempt",
    "PasswordResetToken",
    "Review",
    "ShortlistEvent",
    "UserAccount",
    "UserProfile",
    "ViewEvent",
    "db",
]
