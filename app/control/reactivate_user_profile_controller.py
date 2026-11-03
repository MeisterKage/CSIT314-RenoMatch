from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserProfileEntity


class ReactivateUserProfileController:
    """US-30: an administrator reactivates a suspended profile."""

    def __init__(self):
        self.entity = UserProfileEntity

    def reactivateUserProfile(self, profileId: int, adminId: int) -> bool:
        profile = self.entity.findById(profileId)
        if profile is None:
            raise ValidationError({"profile": "Profile not found."})
        if profile.status != "Suspended":
            raise ValidationError({"profile": "That profile is not suspended."})
        profile.reactivate()
        AuditLogEntity.recordAction(
            adminId,
            "reactivate_profile",
            "user_profile",
            profileId,
            f"Reactivated {profile.name}",
        )
        return True
