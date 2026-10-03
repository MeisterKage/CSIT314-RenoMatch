"""Field rules shared by controllers. Each returns an error message, or None if valid."""

import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_]{3,30}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_PATTERN = re.compile(r"\+?[0-9 ]{8,15}")


def username_problem(username: str) -> str | None:
    if not USERNAME_PATTERN.fullmatch(username):
        return "Username must be 3-30 letters, digits or underscores."
    return None


def email_problem(email: str) -> str | None:
    if not EMAIL_PATTERN.fullmatch(email):
        return "Enter a valid email address."
    return None


def password_problem(password: str) -> str | None:
    if (
        len(password) < 8
        or not any(c.isalpha() for c in password)
        or not any(c.isdigit() for c in password)
    ):
        return "Password must be at least 8 characters and include a letter and a digit."
    return None


def phone_problem(phone: str) -> str | None:
    if phone and not PHONE_PATTERN.fullmatch(phone):
        return "Phone number must be 8-15 digits, optionally starting with +."
    return None
