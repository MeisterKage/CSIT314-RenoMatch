from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserAccountEntity


class UnlockUserAccountController:
    """US-33: an administrator unlocks an account locked by repeated failed logins."""

    def __init__(self):
        self.entity = UserAccountEntity

    def unlockUserAccount(self, userId: int, adminId: int) -> bool:
        account = self.entity.findById(userId)
        if account is None:
            raise ValidationError({"account": "Account not found."})
        if not account.isLocked():
            raise ValidationError({"account": "That account is not locked."})
        account.unlock()
        AuditLogEntity.recordAction(
            adminId, "unlock_account", "user_account", userId, f"Unlocked {account.username}"
        )
        return True
