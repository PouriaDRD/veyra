"""Tests for scoring domain value objects."""

import pytest

from veyra.domain.scoring import (
    ScoringFeature,
    ScoringSourceKind,
)


def test_scoring_feature_exposes_confidence_adjusted_weight() -> None:
    feature = ScoringFeature(
        key="occupation:match",
        value=0.8,
        weight=2.0,
        confidence=0.75,
        reason="Occupation matches the requested profile.",
        source_kind=ScoringSourceKind.FACT,
        source_key="occupation",
    )

    assert feature.effective_weight == pytest.approx(
        1.5,
    )
    assert feature.weighted_value == pytest.approx(
        1.2,
    )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (-0.1, "value must be between 0 and 1"),
        (1.1, "value must be between 0 and 1"),
    ],
)
def test_scoring_feature_rejects_invalid_value(
    value: float,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        ScoringFeature(
            key="feature",
            value=value,
            weight=1.0,
            confidence=1.0,
            reason="reason",
            source_kind=ScoringSourceKind.DERIVED,
        )


@pytest.mark.parametrize(
    ("confidence", "message"),
    [
        (-0.1, "confidence must be between 0 and 1"),
        (1.1, "confidence must be between 0 and 1"),
    ],
)
def test_scoring_feature_rejects_invalid_confidence(
    confidence: float,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        ScoringFeature(
            key="feature",
            value=0.5,
            weight=1.0,
            confidence=confidence,
            reason="reason",
            source_kind=ScoringSourceKind.DERIVED,
        )


def test_scoring_feature_rejects_negative_weight() -> None:
    with pytest.raises(
        ValueError,
        match="weight must be non-negative",
    ):
        ScoringFeature(
            key="feature",
            value=1.0,
            weight=-1.0,
            confidence=1.0,
            reason="reason",
            source_kind=ScoringSourceKind.DERIVED,
        )


@pytest.mark.parametrize(
    ("key", "reason", "message"),
    [
        (" ", "reason", "key must not be empty"),
        ("feature", " ", "reason must not be empty"),
    ],
)
def test_scoring_feature_rejects_empty_required_text(
    key: str,
    reason: str,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        ScoringFeature(
            key=key,
            value=1.0,
            weight=1.0,
            confidence=1.0,
            reason=reason,
            source_kind=ScoringSourceKind.DERIVED,
        )
