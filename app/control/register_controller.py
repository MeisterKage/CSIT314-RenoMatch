from app.control.errors import ValidationError
from app.control.validation import (
    email_problem,
    password_problem,
    phone_problem,
    username_problem,
)
from app.entity import UserAccountEntity, UserProfileEntity

REGISTRABLE_ROLES = ("customer", "designer")


class RegisterController:
    """US03: a visitor registers as a customer or interior designer."""

    def register(
        self, username, email, password, confirm_password, full_name, phone, role
    ) -> UserAccountEntity:
        username, email = username.strip(), email.strip().lower()
        full_name, phone = full_name.strip(), phone.strip()
        errors = {}

        if problem := username_problem(username):
            errors["username"] = problem
        elif UserAccountEntity.findByUsername(username):
            errors["username"] = "That username is taken."

        if problem := email_problem(email):
            errors["email"] = problem
        elif UserAccountEntity.findByEmail(email):
            errors["email"] = "An account with that email already exists."

        if problem := password_problem(password):
            errors["password"] = problem
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not full_name:
            errors["full_name"] = "Enter your full name."
        if problem := phone_problem(phone):
            errors["phone"] = problem

        profile = None
        if role not in REGISTRABLE_ROLES:
            errors["role"] = "Choose customer or interior designer."
        else:
            profile = UserProfileEntity.findDefaultForRole(role)
            if profile is None or profile.status != "Active":
                errors["role"] = "Registration for this role is currently closed."

        if errors:
            raise ValidationError(errors)
        account = UserAccountEntity.createUserAccount(
            username=username,
            email=email,
            password=password,
            name=full_name,
            profile=profile,
            phone=phone,
            recordRegistration=True,  # counted by US-56, saved in the account's own commit
        )
        return account
