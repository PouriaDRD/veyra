"""Tests for location intelligence signals."""

import pytest

from veyra.domain.intelligence import (
    LocationSignal,
    LocationSignalKind,
)


def test_location_signal_normalizes_value() -> None:
    signal = LocationSignal(
        kind=LocationSignalKind.GEOTAG,
        value="  Tehran ",
        weight=0.75,
        confidence=0.9,
    )

    assert signal.value == "tehran"


def test_location_signal_normalizes_context() -> None:
    signal = LocationSignal(
        kind=LocationSignalKind.BIO_MENTION,
        value="tehran",
        weight=0.35,
        confidence=0.8,
        context="  I love Tehran  ",
    )

    assert signal.context == "I love Tehran"


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("weight", -0.01),
        ("weight", 1.01),
        ("confidence", -0.01),
        ("confidence", 1.01),
    ),
)
def test_location_signal_rejects_invalid_scores(
    field_name: str,
    value: float,
) -> None:
    values = {
        "weight": 0.5,
        "confidence": 0.8,
    }

    values[field_name] = value

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        LocationSignal(
            kind=LocationSignalKind.GEOTAG,
            value="tehran",
            weight=values["weight"],
            confidence=values["confidence"],
        )


def test_location_signal_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        LocationSignal(
            kind=LocationSignalKind.GEOTAG,
            value="   ",
            weight=0.5,
            confidence=0.8,
        )
