from app.control.errors import LoginError
from app.entity import UserAccount


class LoginController:
    """US01: log in with username and password."""

    def login(self, username: str, password: str) -> UserAccount:
        account = UserAccount.find_by_username(username)
        if account is None or not account.check_password(password):
            raise LoginError("Invalid username or password.")
        if not account.can_log_in():
            raise LoginError("This account is suspended. Please contact an administrator.")
        return account

    def get_active_account(self, account_id: int) -> UserAccount | None:
        account = UserAccount.find_by_id(account_id)
        if account is None or not account.can_log_in():
            return None
        return account
