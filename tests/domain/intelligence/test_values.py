"""Tests for intelligence value objects."""

import pytest

from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisScore,
    HypothesisStatus,
)


def test_hypothesis_score_preserves_probability_and_confidence() -> None:
    hypothesis = HypothesisScore(
        kind=HypothesisKind.RELATIONSHIP_STATUS,
        value="single",
        probability=0.68,
        confidence=0.42,
        status=HypothesisStatus.POSSIBLE,
        evidence_count=3,
    )

    assert hypothesis.value == "single"
    assert hypothesis.probability == 0.68
    assert hypothesis.confidence == 0.42
    assert hypothesis.evidence_count == 3


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("probability", -0.01),
        ("probability", 1.01),
        ("confidence", -0.01),
        ("confidence", 1.01),
    ),
)
def test_hypothesis_score_rejects_invalid_probability_fields(
    field_name: str,
    value: float,
) -> None:
    values = {
        "probability": 0.5,
        "confidence": 0.5,
    }

    values[field_name] = value

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        HypothesisScore(
            kind=HypothesisKind.RELATIONSHIP_STATUS,
            value="single",
            probability=values["probability"],
            confidence=values["confidence"],
            status=HypothesisStatus.POSSIBLE,
        )


def test_hypothesis_score_requires_non_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="value must not be empty",
    ):
        HypothesisScore(
            kind=HypothesisKind.RELATIONSHIP_STATUS,
            value=" ",
            probability=0.5,
            confidence=0.5,
            status=HypothesisStatus.POSSIBLE,
        )
