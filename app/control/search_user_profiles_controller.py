from app.entity import UserProfileEntity
from app.entity.user_profile import PROFILE_STATUSES, ROLE_TYPES


class SearchUserProfilesController:
    """US-31: an administrator searches profiles by keyword, role type and status."""

    roleTypes = ROLE_TYPES
    statuses = PROFILE_STATUSES

    def __init__(self):
        self.entity = UserProfileEntity

    def searchUserProfiles(self, keyword: str, role: str, status: str):
        return self.entity.searchUserProfiles(keyword, role, status)
