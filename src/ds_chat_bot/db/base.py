"""SQLAlchemy declarative base helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for application-side defaults."""

    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
