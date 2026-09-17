"""Tests for the generic explainable hypothesis engine."""

import pytest

from veyra.domain.intelligence import (
    HypothesisDefinition,
    HypothesisEngine,
    HypothesisEnginePolicy,
    HypothesisKind,
    HypothesisObservation,
    HypothesisStatus,
    ObservationPolarity,
)


def build_location_definition() -> HypothesisDefinition:
    """Create a generic location hypothesis definition."""

    return HypothesisDefinition(
        kind=HypothesisKind.LIKELY_LOCATION,
        allowed_values=(
            "tehran",
            "karaj",
            "shiraz",
            "unknown",
        ),
    )


def build_profile_purpose_definition() -> HypothesisDefinition:
    """Create a generic profile-purpose hypothesis definition."""

    return HypothesisDefinition(
        kind=HypothesisKind.PROFILE_PURPOSE,
        allowed_values=(
            "personal",
            "professional",
            "business",
            "unknown",
        ),
    )


def test_engine_returns_unknown_without_observations() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (),
    )

    assert result.status is HypothesisStatus.UNKNOWN
    assert result.best_value == "unknown"
    assert result.confidence == 0.0


def test_engine_supports_location_hypothesis() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.9,
                confidence=0.95,
                source="bio",
                explanation="Bio explicitly mentions Tehran.",
            ),
        ),
    )

    tehran = result.candidate_for("tehran")

    assert tehran is not None

    assert tehran.support == 0.855
    assert tehran.opposition == 0.0
    assert tehran.score == 0.855

    assert result.best_value == "tehran"

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_multiple_supporting_observations_corroborate_candidate() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.6,
                confidence=0.8,
                source="bio",
                explanation="Bio location signal.",
            ),
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.5,
                confidence=0.8,
                source="geotag",
                explanation="Repeated public geotag signal.",
            ),
        ),
    )

    tehran = result.candidate_for("tehran")

    assert tehran is not None

    assert tehran.support > 0.48
    assert len(tehran.supporting_observations) == 2


def test_opposition_reduces_candidate_score() -> None:
    engine = HypothesisEngine()

    without_opposition = engine.evaluate(
        build_profile_purpose_definition(),
        (
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=1.0,
                source="bio",
                explanation="Professional title.",
            ),
        ),
    )

    with_opposition = engine.evaluate(
        build_profile_purpose_definition(),
        (
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=1.0,
                source="bio",
                explanation="Professional title.",
            ),
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.OPPOSE,
                weight=0.5,
                confidence=1.0,
                source="content",
                explanation="Content contradicts professional profile.",
            ),
        ),
    )

    first = without_opposition.candidate_for("professional")

    second = with_opposition.candidate_for("professional")

    assert first is not None
    assert second is not None

    assert second.score < first.score
    assert second.opposition == 0.5


def test_engine_detects_competing_strong_candidates() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=0.9,
                source="bio",
                explanation="Tehran signal.",
            ),
            HypothesisObservation(
                target_value="karaj",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=0.9,
                source="geotag",
                explanation="Karaj signal.",
            ),
        ),
    )

    assert result.status is HypothesisStatus.CONFLICTED


def test_engine_rejects_unknown_target_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported target values",
    ):
        HypothesisEngine().evaluate(
            build_location_definition(),
            (
                HypothesisObservation(
                    target_value="london",
                    polarity=ObservationPolarity.SUPPORT,
                    weight=0.8,
                    confidence=0.8,
                    source="test",
                    explanation="Unsupported candidate.",
                ),
            ),
        )


def test_engine_is_domain_agnostic() -> None:
    engine = HypothesisEngine()

    location = engine.evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=0.9,
                source="bio",
                explanation="Location signal.",
            ),
        ),
    )

    purpose = engine.evaluate(
        build_profile_purpose_definition(),
        (
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=0.9,
                source="bio",
                explanation="Professional signal.",
            ),
        ),
    )

    assert location.kind is HypothesisKind.LIKELY_LOCATION

    assert purpose.kind is HypothesisKind.PROFILE_PURPOSE

    assert location.best_value == "tehran"
    assert purpose.best_value == "professional"


def test_custom_policy_changes_status_thresholds() -> None:
    engine = HypothesisEngine(
        policy=HypothesisEnginePolicy(
            possible_threshold=0.1,
            probable_threshold=0.3,
            strong_threshold=0.5,
            conflict_threshold=0.4,
            algorithm_version="test-v2",
        )
    )

    result = engine.evaluate(
        build_profile_purpose_definition(),
        (
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.6,
                confidence=1.0,
                source="bio",
                explanation="Professional signal.",
            ),
        ),
    )

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED

    assert result.algorithm_version == "test-v2"


def test_correlated_candidate_fanout_does_not_inflate_confidence() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.45,
                confidence=1.0,
                source="broad_signal",
                explanation="One ambiguous broad signal.",
                correlation_key="signal:1",
                conflict_eligible=False,
            ),
            HypothesisObservation(
                target_value="karaj",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.45,
                confidence=1.0,
                source="broad_signal",
                explanation="Same ambiguous broad signal.",
                correlation_key="signal:1",
                conflict_eligible=False,
            ),
            HypothesisObservation(
                target_value="shiraz",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.45,
                confidence=1.0,
                source="broad_signal",
                explanation="Same ambiguous broad signal.",
                correlation_key="signal:1",
                conflict_eligible=False,
            ),
        ),
    )

    assert result.confidence == 0.45


def test_equal_ambiguous_candidates_are_not_conflicted() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.45,
                confidence=1.0,
                source="broad_signal",
                explanation="Ambiguous candidate.",
                correlation_key="signal:1",
                conflict_eligible=False,
            ),
            HypothesisObservation(
                target_value="karaj",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.45,
                confidence=1.0,
                source="broad_signal",
                explanation="Ambiguous candidate.",
                correlation_key="signal:1",
                conflict_eligible=False,
            ),
        ),
    )

    assert result.status is HypothesisStatus.AMBIGUOUS

    assert result.best_value == "unknown"


def test_two_explicit_competing_candidates_remain_conflicted() -> None:
    result = HypothesisEngine().evaluate(
        build_location_definition(),
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=1.0,
                confidence=0.95,
                source="explicit",
                explanation="Explicit claim.",
                correlation_key="evidence:1",
                conflict_eligible=True,
            ),
            HypothesisObservation(
                target_value="karaj",
                polarity=ObservationPolarity.SUPPORT,
                weight=1.0,
                confidence=0.95,
                source="explicit",
                explanation="Competing explicit claim.",
                correlation_key="evidence:2",
                conflict_eligible=True,
            ),
        ),
    )

    assert result.status is HypothesisStatus.CONFLICTED
