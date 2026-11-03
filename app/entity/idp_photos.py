"""Photo files for IDPs (US-38, US-40, US-45): checking, saving and deleting.

Photos are saved in the upload folder with a random name and served from /uploads/<name>.
"""

import os
import secrets

from flask import current_app

MAX_PHOTO_BYTES = 5 * 1024 * 1024
UPLOAD_URL_PREFIX = "/uploads/"
EXTENSIONS = {"png": ".png", "jpg": ".jpg"}
ACCEPTED_EXTENSIONS = {".png": "png", ".jpg": "jpg", ".jpeg": "jpg"}


def detectImageType(file) -> str | None:
    """The real type of an uploaded file from its first bytes: "png", "jpg" or None."""
    stream = file.stream
    stream.seek(0)
    head = stream.read(8)
    stream.seek(0)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    return None


def sizeInBytes(file) -> int:
    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    return size


def isAcceptablePhoto(file) -> bool:
    """True for a JPG or PNG of at most 5 MB, judged by extension and real content."""
    extension = os.path.splitext(file.filename or "")[1].lower()
    kind = detectImageType(file)
    return (
        kind is not None
        and ACCEPTED_EXTENSIONS.get(extension) == kind
        and 0 < sizeInBytes(file) <= MAX_PHOTO_BYTES
    )


def savePhoto(file) -> str:
    """Save an acceptable photo under a random name and return its /uploads/ URL."""
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    name = secrets.token_hex(16) + EXTENSIONS[detectImageType(file)]
    file.stream.seek(0)
    file.save(os.path.join(folder, name))
    return UPLOAD_URL_PREFIX + name


def deletePhoto(url: str) -> None:
    """Delete the saved file behind a /uploads/ URL. A missing file is ignored."""
    if not url.startswith(UPLOAD_URL_PREFIX):
        return
    name = os.path.basename(url[len(UPLOAD_URL_PREFIX):])
    try:
        os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    except OSError:
        pass
