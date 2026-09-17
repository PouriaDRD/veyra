"""Custom SQLAlchemy database types."""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """
    Persist timezone-aware datetimes as normalized UTC values.

    SQLite does not preserve timezone information. Values are therefore
    stored as naive UTC and restored as timezone-aware UTC datetimes.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        """Normalize bound datetime values to naive UTC."""

        del dialect

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "UTCDateTime requires a timezone-aware datetime.",
            )

        return value.astimezone(UTC).replace(
            tzinfo=None,
        )

    def process_result_value(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        """Restore database datetime values as timezone-aware UTC."""

        del dialect

        if value is None:
            return None

        return value.replace(
            tzinfo=UTC,
        )
