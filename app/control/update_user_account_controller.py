from app.control.errors import ValidationError
from app.control.validation import email_problem, phone_problem
from app.entity import AuditLogEntity, UserAccountEntity, UserProfileEntity


class UpdateUserAccountController:
    """US-22: an administrator updates the details and profile of an account."""

    def __init__(self):
        self.entity = UserAccountEntity

    def updateUserAccount(self, userId, name, email, phone, profileId, adminId) -> bool:
        account = self.entity.findById(userId)
        if account is None:
            raise ValidationError({"account": "Account not found."})
        if account.isAnonymised:
            raise ValidationError({"account": "A deleted account cannot be changed."})
        name, email, phone = name.strip(), email.strip().lower(), phone.strip()
        errors = {}
        if not name:
            errors["name"] = "Enter the full name."
        if problem := email_problem(email):
            errors["email"] = problem
        else:
            owner = self.entity.findByEmail(email)
            if owner is not None and owner.userId != userId:
                errors["email"] = "An account with that email already exists."
        if problem := phone_problem(phone):
            errors["phone"] = problem
        profile = UserProfileEntity.findById(profileId) if profileId else None
        if profile is None:
            errors["profileId"] = "Choose a profile."
        elif profile.profileId != account.profileId:
            if userId == adminId:
                errors["profileId"] = "You cannot move your own account to another profile."
            elif profile.status != "Active":
                errors["profileId"] = "That profile is suspended. Choose another."
        if errors:
            raise ValidationError(errors)
        account.updateUserAccount(name, email, phone, profile)
        AuditLogEntity.recordAction(
            adminId,
            "update_account",
            "user_account",
            userId,
            f"Updated {account.username}, profile {profile.name}",
        )
        return True
