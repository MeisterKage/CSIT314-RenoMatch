from app.entity import UserProfileEntity


class ViewUserProfileController:
    """US-27: an administrator views one profile with its role and account count."""

    def __init__(self):
        self.entity = UserProfileEntity

    def getUserProfile(self, profileId: int):
        return self.entity.findById(profileId)
