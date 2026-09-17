"""Tests for birth-year value objects."""

import pytest

from veyra.domain.evidence import (
    BirthYear,
    CalendarSystem,
)


def test_birth_year_preserves_calendar() -> None:
    value = BirthYear(
        year=1388,
        calendar=CalendarSystem.SOLAR_HIJRI,
    )

    assert value.year == 1388
    assert value.calendar is CalendarSystem.SOLAR_HIJRI


def test_birth_year_rejects_invalid_year() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        BirthYear(
            year=0,
            calendar=CalendarSystem.GREGORIAN,
        )
