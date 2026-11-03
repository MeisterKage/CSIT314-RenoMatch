"""Transient report classes. They are built from PlatformActivityEntity and other
entities on demand and never stored."""

from dataclasses import dataclass, field
from datetime import date

# The report figures in display order, with their labels (US-55, US-56, US-59).
REPORT_FIGURES = (
    ("newUsers", "New registered users"),
    ("newDesigners", "New designers"),
    ("newIDPs", "New IDPs"),
    ("idpViews", "IDP views"),
    ("shortlists", "Shortlists"),
    ("enquiries", "Enquiries"),
)


@dataclass
class Report:
    """Platform figures for one period (daily, monthly or custom range).

    `previous` holds the same figures for the period before, for comparison.
    """

    reportType: str  # "daily", "monthly" or "custom"
    startDate: date
    endDate: date
    newUsers: int = 0
    newDesigners: int = 0
    newIDPs: int = 0
    idpViews: int = 0
    shortlists: int = 0
    enquiries: int = 0
    previous: "Report | None" = None

    @property
    def hasActivity(self) -> bool:
        return any(getattr(self, figure) for figure, _ in REPORT_FIGURES)

    def change(self, figure: str) -> int:
        """This period's figure minus the previous period's (0 with no previous period)."""
        if self.previous is None:
            return 0
        return getattr(self, figure) - getattr(self.previous, figure)


@dataclass
class Summary:
    """A designer's weekly interest figures for the summary email (US-48)."""

    designerId: int
    startDate: date
    endDate: date
    designerName: str = ""
    totalViews: int = 0
    totalShortlists: int = 0
    topIDPs: list[tuple[str, int]] = field(default_factory=list)  # (title, views), top 3

    @property
    def hasActivity(self) -> bool:
        return bool(self.totalViews or self.totalShortlists)
