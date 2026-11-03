from app.control.errors import LoginError
from app.entity import UserAccountEntity


class LoginController:
    """US01: log in with username and password."""

    def login(self, username: str, password: str) -> UserAccountEntity:
        account = UserAccountEntity.findByUsername(username)
        if account is None or not account.checkPassword(password):
            raise LoginError("Invalid username or password.")
        if not account.canLogIn():
            raise LoginError("This account is suspended. Please contact an administrator.")
        return account

    def get_active_account(self, account_id: int) -> UserAccountEntity | None:
        account = UserAccountEntity.findById(account_id)
        if account is None or not account.canLogIn():
            return None
        return account
