"""The tools each role's home page lists, with the sprint that delivers them.

Sprint numbers follow section 7 of the design spec. A tool with an endpoint is
available now and links to its page.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    sprint: int | None = None
    endpoint: str | None = None

    @property
    def available(self) -> bool:
        return self.endpoint is not None

    @property
    def status(self) -> str:
        return "Available" if self.available else f"Coming in Sprint {self.sprint}"


CHANGE_PASSWORD = Tool(
    "Change password",
    "Set a new password for your account.",
    endpoint="auth.change_password",
)
