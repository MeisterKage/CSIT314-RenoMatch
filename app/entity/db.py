from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow() -> datetime:
    """Current UTC time without tzinfo (SQLite stores naive datetimes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
