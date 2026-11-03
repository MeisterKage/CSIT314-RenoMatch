from app.entity import UserAccountEntity


class SearchUserAccountsController:
    """US-25: an administrator searches accounts by keyword, profile name and status."""

    def __init__(self):
        self.entity = UserAccountEntity

    def searchUserAccounts(self, keyword: str, profile: str, status: str):
        return self.entity.searchUserAccounts(keyword, profile, status)
