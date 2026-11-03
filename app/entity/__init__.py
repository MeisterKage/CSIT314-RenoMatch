"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.audit_log import AuditLogEntity
from app.entity.category import CategoryEntity
from app.entity.company_info import CompanyInfoEntity
from app.entity.db import db
from app.entity.enquiry import EnquiryEntity
from app.entity.enquiry_message import EnquiryMessageEntity
from app.entity.favourite import FavouriteEntity
from app.entity.idp import IDPEntity
from app.entity.idp_flag import IDPFlagEntity
from app.entity.login_attempt import LoginAttemptEntity
from app.entity.platform_activity import PlatformActivityEntity
from app.entity.review import ReviewEntity
from app.entity.user_account import UserAccountEntity
from app.entity.user_profile import UserProfileEntity

__all__ = [
    "AuditLogEntity",
    "CategoryEntity",
    "CompanyInfoEntity",
    "EnquiryEntity",
    "EnquiryMessageEntity",
    "FavouriteEntity",
    "IDPEntity",
    "IDPFlagEntity",
    "LoginAttemptEntity",
    "PlatformActivityEntity",
    "ReviewEntity",
    "UserAccountEntity",
    "UserProfileEntity",
    "db",
]
