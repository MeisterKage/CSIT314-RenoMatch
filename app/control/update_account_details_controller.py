from app.control.errors import ValidationError
from app.control.validation import email_problem, phone_problem
from app.entity import UserAccountEntity


class UpdateAccountDetailsController:
    """US-07: a user updates their own name, email and phone. Designers also set the weekly
    summary opt-in."""

    def __init__(self):
        self.entity = UserAccountEntity

    def updateAccountDetails(self, userId: int, name: str, email: str, phone: str) -> bool:
        account = self.entity.findById(userId)
        name, email, phone = name.strip(), email.strip().lower(), phone.strip()
        errors = {}
        if not name:
            errors["name"] = "Enter your full name."
        if problem := email_problem(email):
            errors["email"] = problem
        else:
            owner = self.entity.findByEmail(email)
            if owner is not None and owner.userId != userId:
                errors["email"] = "An account with that email already exists."
        if problem := phone_problem(phone):
            errors["phone"] = problem
        if errors:
            raise ValidationError(errors)
        account.updateDetails(name, email, phone)
        return True

    def setWeeklySummaryOptIn(self, userId: int, optIn: bool) -> bool:
        self.entity.findById(userId).setWeeklySummaryOptIn(optIn)
        return True
