"""Checks shared by AddIDPController and UpdateIDPController (US-38, US-40, US-45)."""

from app.entity.idp import IDP_STAGES, PROPERTY_TYPES, STYLES
from app.entity.idp_photos import isAcceptablePhoto

TITLE_MAX = 120
LOCATION_MAX = 60
INVALID_PHOTO = 'Photo "{name}" must be a JPG or PNG file of 5 MB or less.'


def findMissingFields(idp: dict, photoCount: int) -> list[str]:
    """Names of the required fields that are blank or not valid, in form order (6a).

    "photos" is listed when the IDP would have no photo at all.
    """
    missing = []

    def text(name, maxLength=None):
        value = str(idp.get(name) or "").strip()
        if not value or (maxLength and len(value) > maxLength):
            missing.append(name)

    text("title", TITLE_MAX)
    text("description")
    if not _isPositiveInt(idp.get("categoryId")):
        missing.append("categoryId")
    if idp.get("style") not in STYLES:
        missing.append("style")
    if idp.get("propertyType") not in PROPERTY_TYPES:
        missing.append("propertyType")
    if not _isPositiveNumber(idp.get("budget")):
        missing.append("budget")
    text("location", LOCATION_MAX)
    if (idp.get("stage") or "Current") not in IDP_STAGES:
        missing.append("stage")
    if photoCount < 1:
        missing.append("photos")
    return missing


def findInvalidPhoto(photos: list) -> str | None:
    """A message naming the first photo that is not a JPG or PNG of at most 5 MB (6b)."""
    for photo in photos:
        if not isAcceptablePhoto(photo):
            return INVALID_PHOTO.format(name=photo.filename)
    return None


def _isPositiveInt(value) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _isPositiveNumber(value) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return 0 < number < 1e12
