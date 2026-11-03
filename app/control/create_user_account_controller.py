from app.control.errors import ValidationError
from app.control.validation import (
    email_problem,
    password_problem,
    phone_problem,
    username_problem,
)
from app.entity import AuditLogEntity, UserAccountEntity, UserProfileEntity


class CreateUserAccountController:
    """US-20: an administrator creates an account with any active profile."""

    def __init__(self):
        self.entity = UserAccountEntity

    def createUserAccount(
        self, username, email, password, name, profileId, phone, adminId
    ) -> UserAccountEntity:
        username, email = username.strip(), email.strip().lower()
        name, phone = name.strip(), phone.strip()
        errors = {}
        if problem := username_problem(username):
            errors["username"] = problem
        elif self.entity.findByUsername(username):
            errors["username"] = "That username is taken."
        if problem := email_problem(email):
            errors["email"] = problem
        elif self.entity.findByEmail(email):
            errors["email"] = "An account with that email already exists."
        if problem := password_problem(password):
            errors["password"] = problem
        if not name:
            errors["name"] = "Enter the full name."
        if problem := phone_problem(phone):
            errors["phone"] = problem
        profile = UserProfileEntity.findById(profileId) if profileId else None
        if profile is None:
            errors["profileId"] = "Choose a profile."
        elif profile.status != "Active":
            errors["profileId"] = "That profile is suspended. Choose another."
        if errors:
            raise ValidationError(errors)
        account = self.entity.createUserAccount(
            username=username,
            email=email,
            password=password,
            name=name,
            profile=profile,
            phone=phone,
        )
        AuditLogEntity.recordAction(
            adminId,
            "create_account",
            "user_account",
            account.userId,
            f"Created {account.username} with profile {profile.name}",
        )
        return account
