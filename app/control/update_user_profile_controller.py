from app.control.create_user_profile_controller import profile_errors
from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserProfileEntity


class UpdateUserProfileController:
    """US-28: an administrator changes the name and description of a profile."""

    def __init__(self):
        self.entity = UserProfileEntity

    def updateUserProfile(self, profileId, name, description, adminId) -> bool:
        profile = self.entity.findById(profileId)
        if profile is None:
            raise ValidationError({"profile": "Profile not found."})
        name, description = name.strip(), description.strip()
        errors = profile_errors(self.entity, name, description, profileId)
        if errors:
            raise ValidationError(errors)
        profile.updateUserProfile(name, description)
        AuditLogEntity.recordAction(
            adminId, "update_profile", "user_profile", profileId, f"Updated {profile.name}"
        )
        return True
