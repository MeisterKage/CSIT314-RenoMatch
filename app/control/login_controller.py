from app.control.errors import LoginError
from app.entity import LoginAttemptEntity, UserAccountEntity

LOCKED_MESSAGE = "This account is locked. Try again later or contact an administrator."


class LoginController:
    """US-03: log in with username and password. Five failed logins in a row lock the
    account for 15 minutes (until an administrator unlocks it, US-33). Every attempt is
    recorded as a LoginAttemptEntity."""

    def login(self, username: str, password: str) -> UserAccountEntity:
        account = UserAccountEntity.findByUsername(username)
        if account is None:
            LoginAttemptEntity.recordAttempt(username, None, False)
            raise LoginError("Invalid username or password.")
        if account.isLocked():
            LoginAttemptEntity.recordAttempt(username, account.userId, False)
            raise LoginError(LOCKED_MESSAGE)
        if not account.checkPassword(password):
            account.registerFailedLogin()
            LoginAttemptEntity.recordAttempt(username, account.userId, False)
            if account.isLocked():
                raise LoginError(LOCKED_MESSAGE)
            raise LoginError("Invalid username or password.")
        if not account.canLogIn():
            LoginAttemptEntity.recordAttempt(username, account.userId, False)
            raise LoginError("This account is suspended. Please contact an administrator.")
        account.resetFailedLogins()
        LoginAttemptEntity.recordAttempt(username, account.userId, True)
        return account

    def get_active_account(self, account_id: int) -> UserAccountEntity | None:
        account = UserAccountEntity.findById(account_id)
        if account is None or not account.canLogIn():
            return None
        return account
