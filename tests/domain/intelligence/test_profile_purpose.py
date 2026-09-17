"""Tests for profile-purpose signal values."""

import pytest

from veyra.domain.intelligence import (
    ProfilePurpose,
    ProfilePurposeSignalKind,
)
from veyra.domain.intelligence.profile_purpose import (
    ProfilePurposeSignal,
)


def test_signal_normalizes_raw_value_and_context() -> None:
    signal = ProfilePurposeSignal(
        kind=ProfilePurposeSignalKind.PROFESSIONAL_ROLE,
        purpose=ProfilePurpose.PROFESSIONAL,
        weight=0.65,
        confidence=0.90,
        raw_value="  Software Engineer  ",
        context="  Software Engineer | Tehran  ",
    )

    assert signal.raw_value == "Software Engineer"
    assert signal.context == "Software Engineer | Tehran"


@pytest.mark.parametrize(
    "weight",
    (
        -0.1,
        1.1,
    ),
)
def test_rejects_invalid_weight(
    weight: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="weight",
    ):
        ProfilePurposeSignal(
            kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
            purpose=ProfilePurpose.BUSINESS,
            weight=weight,
            confidence=0.90,
            raw_value="shop",
        )


@pytest.mark.parametrize(
    "confidence",
    (
        -0.1,
        1.1,
    ),
)
def test_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        ProfilePurposeSignal(
            kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=confidence,
            raw_value="shop",
        )


def test_rejects_unknown_target() -> None:
    with pytest.raises(
        ValueError,
        match="UNKNOWN",
    ):
        ProfilePurposeSignal(
            kind=ProfilePurposeSignalKind.PERSONAL_MARKER,
            purpose=ProfilePurpose.UNKNOWN,
            weight=0.50,
            confidence=0.90,
            raw_value="personal",
        )


def test_rejects_empty_raw_value() -> None:
    with pytest.raises(
        ValueError,
        match="raw_value",
    ):
        ProfilePurposeSignal(
            kind=ProfilePurposeSignalKind.PERSONAL_MARKER,
            purpose=ProfilePurpose.PERSONAL,
            weight=0.50,
            confidence=0.90,
            raw_value="   ",
        )


def test_empty_context_normalizes_to_none() -> None:
    signal = ProfilePurposeSignal(
        kind=ProfilePurposeSignalKind.CREATOR_MARKER,
        purpose=ProfilePurpose.CREATOR,
        weight=0.85,
        confidence=0.95,
        raw_value="creator",
        context="   ",
    )

    assert signal.context is None
