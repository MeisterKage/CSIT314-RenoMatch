from app.control.errors import ValidationError
from app.entity import AuditLogEntity, UserAccountEntity


class ReactivateUserAccountController:
    """US-24: an administrator reactivates a suspended account."""

    def __init__(self):
        self.entity = UserAccountEntity

    def reactivateUserAccount(self, userId: int, adminId: int) -> bool:
        account = self.entity.findById(userId)
        if account is None:
            raise ValidationError({"account": "Account not found."})
        if account.status == "Active":
            raise ValidationError({"account": "That account is already active."})
        account.reactivate()
        AuditLogEntity.recordAction(
            adminId,
            "reactivate_account",
            "user_account",
            userId,
            f"Reactivated {account.username}",
        )
        return True
