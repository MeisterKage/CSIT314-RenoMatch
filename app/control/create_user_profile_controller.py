from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserProfileEntity
from app.entity.user_profile import ROLE_TYPES

NAME_MAX = 60
DESCRIPTION_MAX = 255


def profile_errors(entity, name: str, description: str, exceptProfileId=None) -> dict:
    """The name and description rules shared by create (US-26) and update (US-28)."""
    errors = {}
    if not name:
        errors["name"] = "Enter a profile name."
    elif len(name) > NAME_MAX:
        errors["name"] = f"The name can be at most {NAME_MAX} characters."
    elif entity.nameTaken(name, exceptProfileId):
        errors["name"] = "A profile with that name already exists."
    if len(description) > DESCRIPTION_MAX:
        errors["description"] = f"The description can be at most {DESCRIPTION_MAX} characters."
    return errors


class CreateUserProfileController:
    """US-26: an administrator creates a profile for one role type."""

    def __init__(self):
        self.entity = UserProfileEntity

    def createUserProfile(self, name, description, roleType, adminId) -> UserProfileEntity:
        name, description = name.strip(), description.strip()
        errors = profile_errors(self.entity, name, description)
        if roleType not in ROLE_TYPES:
            errors["roleType"] = "Choose a role."
        if errors:
            raise ValidationError(errors)
        profile = self.entity.createUserProfile(name, roleType, description)
        AuditLogEntity.recordAction(
            adminId,
            "create_profile",
            "user_profile",
            profile.profileId,
            f"Created {profile.name} for role {roleType}",
        )
        return profile
