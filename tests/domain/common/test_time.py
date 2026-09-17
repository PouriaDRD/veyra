"""Tests for domain time utilities."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from veyra.domain.common import ensure_utc_datetime


def test_datetime_is_normalized_to_utc() -> None:
    source_timezone = timezone(
        timedelta(
            hours=3,
            minutes=30,
        )
    )

    value = datetime(
        2026,
        9,
        17,
        12,
        0,
        tzinfo=source_timezone,
    )

    normalized = ensure_utc_datetime(
        value,
        field_name="value",
    )

    assert normalized.tzinfo is UTC

    assert normalized.hour == 8
    assert normalized.minute == 30


def test_naive_datetime_is_rejected() -> None:
    value = datetime(
        2026,
        9,
        17,
        12,
        0,
    )

    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        ensure_utc_datetime(
            value,
            field_name="value",
        )
