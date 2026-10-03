from collections.abc import MutableMapping


class LogoutController:
    """US02: log out so nobody else can use the session."""

    def logout(self, session: MutableMapping) -> None:
        session.clear()
