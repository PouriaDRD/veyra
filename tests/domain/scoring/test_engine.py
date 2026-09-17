"""Tests for the weighted scoring engine."""

import pytest

from veyra.domain.scoring import (
    ScoringFeature,
    ScoringSourceKind,
    WeightedScoringEngine,
)


def feature(
    *,
    key: str,
    value: float,
    weight: float = 1.0,
    confidence: float = 1.0,
) -> ScoringFeature:
    """Build one deterministic scoring feature."""

    return ScoringFeature(
        key=key,
        value=value,
        weight=weight,
        confidence=confidence,
        reason=f"Reason for {key}.",
        source_kind=ScoringSourceKind.FACT,
        source_key=key,
    )


def test_weighted_engine_returns_normalized_zero_to_ten_score() -> None:
    result = WeightedScoringEngine().score(
        (
            feature(
                key="occupation",
                value=1.0,
                weight=2.0,
            ),
            feature(
                key="location",
                value=0.5,
                weight=1.0,
            ),
        )
    )

    assert result.score == 8.333333
    assert result.normalized_value == 0.833333
    assert result.total_effective_weight == 3.0
    assert result.algorithm_version == "scoring-v1"
    assert result.is_scorable is True


def test_confidence_reduces_influence_without_acting_as_negative_evidence() -> None:
    result = WeightedScoringEngine().score(
        (
            feature(
                key="strong",
                value=1.0,
                confidence=1.0,
            ),
            feature(
                key="uncertain",
                value=0.0,
                confidence=0.1,
            ),
        )
    )

    assert result.score == 9.090909
    assert result.total_effective_weight == 1.1


def test_zero_confidence_feature_does_not_change_score() -> None:
    result = WeightedScoringEngine().score(
        (
            feature(
                key="supported",
                value=0.8,
            ),
            feature(
                key="ignored",
                value=0.0,
                weight=100.0,
                confidence=0.0,
            ),
        )
    )

    assert result.score == 8.0
    assert result.total_effective_weight == 1.0


def test_no_effective_weight_returns_unscorable_result() -> None:
    result = WeightedScoringEngine().score(
        (
            feature(
                key="unknown",
                value=1.0,
                confidence=0.0,
            ),
        )
    )

    assert result.score is None
    assert result.normalized_value is None
    assert result.total_effective_weight == 0.0
    assert result.is_scorable is False


def test_empty_features_return_unscorable_result() -> None:
    result = WeightedScoringEngine().score(
        (),
    )

    assert result.score is None
    assert result.contributions == ()
    assert result.is_scorable is False


def test_contributions_are_deterministically_ordered_by_key() -> None:
    result = WeightedScoringEngine().score(
        (
            feature(
                key="z-location",
                value=1.0,
            ),
            feature(
                key="a-occupation",
                value=1.0,
            ),
        )
    )

    assert tuple(contribution.key for contribution in result.contributions) == (
        "a-occupation",
        "z-location",
    )


def test_duplicate_feature_keys_are_rejected() -> None:
    engine = WeightedScoringEngine()

    with pytest.raises(
        ValueError,
        match="Duplicate scoring feature key: occupation",
    ):
        engine.score(
            (
                feature(
                    key="occupation",
                    value=1.0,
                ),
                feature(
                    key="occupation",
                    value=0.5,
                ),
            )
        )


def test_contribution_preserves_explanation_metadata() -> None:
    result = WeightedScoringEngine().score(
        (
            ScoringFeature(
                key="education",
                value=0.75,
                weight=2.0,
                confidence=0.8,
                reason="Education satisfies the configured rule.",
                source_kind=ScoringSourceKind.FACT,
                source_key="education",
            ),
        )
    )

    contribution = result.contributions[0]

    assert contribution.configured_weight == 2.0
    assert contribution.effective_weight == 1.6
    assert contribution.weighted_value == 1.2
    assert contribution.reason == "Education satisfies the configured rule."
    assert contribution.source_kind is ScoringSourceKind.FACT
    assert contribution.source_key == "education"
