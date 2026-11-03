"""Reading report parameters from a request, shared by the report controllers and the page."""

from datetime import date

REPORT_TYPES = ("daily", "monthly", "custom")
FIRST_YEAR = 2000


def parseDate(value) -> date | None:
    """A yyyy-mm-dd date, or None when it is blank or unreadable."""
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def parseMonthYear(month, year) -> tuple[int, int] | None:
    """(month, year) as ints, or None when either is missing or out of range."""
    try:
        monthNumber, yearNumber = int((month or "").strip()), int((year or "").strip())
    except ValueError:
        return None
    if 1 <= monthNumber <= 12 and FIRST_YEAR <= yearNumber <= 9999:
        return monthNumber, yearNumber
    return None


def periodLabel(reportType, params) -> str | None:
    """The period text used in the PDF file name, or None when the parameters are unusable."""
    if reportType == "daily":
        day = parseDate(params.get("date"))
        return day.isoformat() if day else None
    if reportType == "monthly":
        monthYear = parseMonthYear(params.get("month"), params.get("year"))
        return f"{monthYear[1]:04d}-{monthYear[0]:02d}" if monthYear else None
    if reportType == "custom":
        start, end = parseDate(params.get("startDate")), parseDate(params.get("endDate"))
        return f"{start.isoformat()}_to_{end.isoformat()}" if start and end else None
    return None
