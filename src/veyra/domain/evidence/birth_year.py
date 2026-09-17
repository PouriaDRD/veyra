"""Birth-year value objects."""

from dataclasses import dataclass
from enum import StrEnum


class CalendarSystem(StrEnum):
    """Calendar used by an explicit birth-year value."""

    GREGORIAN = "gregorian"
    SOLAR_HIJRI = "solar_hijri"


@dataclass(frozen=True, slots=True)
class BirthYear:
    """Calendar-aware normalized birth year."""

    year: int
    calendar: CalendarSystem

    def __post_init__(self) -> None:
        """Validate the normalized year."""

        if isinstance(self.year, bool) or not isinstance(
            self.year,
            int,
        ):
            raise TypeError(
                "year must be an integer.",
            )

        if self.year <= 0:
            raise ValueError(
                "year must be greater than zero.",
            )
