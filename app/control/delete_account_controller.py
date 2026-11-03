from app.control.errors import ValidationError
from app.entity import UserAccountEntity


class DeleteAccountController:
    """US-08: a user deletes their own account. It is anonymised, not removed."""

    def __init__(self):
        self.entity = UserAccountEntity

    def deleteAccount(self, userId: int, password: str) -> bool:
        account = self.entity.findById(userId)
        if not account.checkPassword(password):
            raise ValidationError({"password": "Your password is incorrect."})
        account.anonymise()
        return True
