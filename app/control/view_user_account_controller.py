from app.entity import UserAccountEntity


class ViewUserAccountController:
    """US-21: an administrator views one account."""

    def __init__(self):
        self.entity = UserAccountEntity

    def getUserAccount(self, userId: int) -> UserAccountEntity | None:
        return self.entity.findById(userId)
