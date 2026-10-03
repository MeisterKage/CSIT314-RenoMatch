class LoginError(Exception):
    """Credentials are wrong or the account is not allowed to log in."""


class ValidationError(Exception):
    """One or more form fields are invalid. `errors` maps field name to message."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors
