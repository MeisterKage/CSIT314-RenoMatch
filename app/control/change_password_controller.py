from app.control.errors import ValidationError
from app.control.validation import password_problem
from app.entity import UserAccountEntity


class ChangePasswordController:
    """US44: a logged-in user changes their own password."""

    def change_password(
        self, account_id: int, current_password: str, new_password: str, confirm_password: str
    ) -> None:
        account = UserAccountEntity.findById(account_id)
        if account is None:
            raise LookupError(f"No account with id {account_id}")

        errors = {}
        if not account.checkPassword(current_password):
            errors["current_password"] = "Current password is incorrect."
        if problem := password_problem(new_password):
            errors["new_password"] = problem
        elif new_password == current_password:
            errors["new_password"] = "New password must be different from the current one."
        elif new_password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            raise ValidationError(errors)
        account.changePassword(new_password)
