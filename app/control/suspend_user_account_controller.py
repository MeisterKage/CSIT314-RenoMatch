from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserAccountEntity


class SuspendUserAccountController:
    """US-23: an administrator suspends an account, but never their own."""

    def __init__(self):
        self.entity = UserAccountEntity

    def suspendUserAccount(self, userId: int, adminId: int) -> bool:
        account = self.entity.findById(userId)
        if account is None:
            raise ValidationError({"account": "Account not found."})
        if userId == adminId:
            raise ValidationError({"account": "You cannot suspend your own account."})
        if account.status == "Suspended":
            raise ValidationError({"account": "That account is already suspended."})
        account.suspend()
        AuditLogEntity.recordAction(
            adminId, "suspend_account", "user_account", userId, f"Suspended {account.username}"
        )
        return True
