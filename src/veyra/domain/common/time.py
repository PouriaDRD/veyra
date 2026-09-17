"""Domain time utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(UTC)


def ensure_utc_datetime(
    value: datetime,
    *,
    field_name: str,
) -> datetime:
    """
    Validate and normalize a datetime to UTC.

    Domain datetimes must always be timezone-aware.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware.",
        )

    return value.astimezone(UTC)
