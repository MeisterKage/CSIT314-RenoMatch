"""The tools each role's home page lists. Every tool links to its page by endpoint."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    endpoint: str


CHANGE_PASSWORD = Tool(
    "Change password",
    "Set a new password for your account.",
    endpoint="auth.change_password",
)
