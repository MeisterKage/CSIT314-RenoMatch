from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserAccountEntity, UserProfileEntity


class SuspendUserProfileController:
    """US-29: an administrator suspends a profile, which blocks login for all its accounts.
    An administrator cannot suspend the profile of their own account."""

    def __init__(self):
        self.entity = UserProfileEntity

    def suspendUserProfile(self, profileId: int, adminId: int) -> bool:
        profile = self.entity.findById(profileId)
        if profile is None:
            raise ValidationError({"profile": "Profile not found."})
        admin = UserAccountEntity.findById(adminId)
        if admin is not None and admin.profileId == profileId:
            raise ValidationError({"profile": "You cannot suspend your own profile."})
        if profile.status == "Suspended":
            raise ValidationError({"profile": "That profile is already suspended."})
        profile.suspend()
        AuditLogEntity.recordAction(
            adminId, "suspend_profile", "user_profile", profileId, f"Suspended {profile.name}"
        )
        return True
