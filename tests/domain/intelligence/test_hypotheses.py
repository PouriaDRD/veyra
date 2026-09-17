"""Tests for generic hypothesis domain models."""

import pytest

from veyra.domain.intelligence import (
    HypothesisCandidateResult,
    HypothesisDefinition,
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
    HypothesisStatus,
    ObservationPolarity,
)


def test_definition_requires_unknown_candidate() -> None:
    with pytest.raises(
        ValueError,
        match="unknown_value must exist",
    ):
        HypothesisDefinition(
            kind=HypothesisKind.LIKELY_LOCATION,
            allowed_values=(
                "tehran",
                "shiraz",
            ),
        )


def test_definition_rejects_duplicate_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        HypothesisDefinition(
            kind=HypothesisKind.LIKELY_LOCATION,
            allowed_values=(
                "tehran",
                "tehran",
                "unknown",
            ),
        )


def test_observation_calculates_effective_strength() -> None:
    observation = HypothesisObservation(
        target_value="tehran",
        polarity=ObservationPolarity.SUPPORT,
        weight=0.8,
        confidence=0.75,
        source="bio",
        explanation="Explicit location mention.",
    )

    assert observation.effective_strength == 0.6


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("weight", -0.01),
        ("weight", 1.01),
        ("confidence", -0.01),
        ("confidence", 1.01),
    ),
)
def test_observation_rejects_invalid_numeric_values(
    field_name: str,
    value: float,
) -> None:
    values = {
        "weight": 0.5,
        "confidence": 0.5,
    }

    values[field_name] = value

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        HypothesisObservation(
            target_value="personal",
            polarity=ObservationPolarity.SUPPORT,
            weight=values["weight"],
            confidence=values["confidence"],
            source="profile",
            explanation="Test observation.",
        )


def test_result_can_find_candidate() -> None:
    candidate = HypothesisCandidateResult(
        value="professional",
        score=0.7,
        support=0.7,
        opposition=0.0,
    )

    result = HypothesisResult(
        kind=HypothesisKind.PROFILE_PURPOSE,
        status=HypothesisStatus.PROBABLE,
        best_value="professional",
        confidence=0.8,
        candidates=(
            candidate,
            HypothesisCandidateResult(
                value="unknown",
                score=0.0,
                support=0.0,
                opposition=0.0,
            ),
        ),
        algorithm_version="test-v1",
    )

    assert (
        result.candidate_for(
            "professional",
        )
        is candidate
    )

    assert (
        result.candidate_for(
            "business",
        )
        is None
    )


def test_open_set_definition_accepts_observed_values() -> None:
    definition = HypothesisDefinition(
        kind=HypothesisKind.LIKELY_LOCATION,
        allowed_values=("unknown",),
        unknown_value="unknown",
        allow_observed_values=True,
    )

    observations = (
        HypothesisObservation(
            target_value="tehran",
            polarity=ObservationPolarity.SUPPORT,
            weight=0.8,
            confidence=0.9,
            source="location_signal",
            explanation="Observed Tehran location evidence.",
        ),
    )

    assert definition.candidate_values(
        observations,
    ) == (
        "unknown",
        "tehran",
    )


def test_open_set_candidate_values_include_observed_values() -> None:
    definition = HypothesisDefinition(
        kind=HypothesisKind.LIKELY_LOCATION,
        allowed_values=("unknown",),
        unknown_value="unknown",
        allow_observed_values=True,
    )

    observations = (
        HypothesisObservation(
            target_value="tehran",
            polarity=ObservationPolarity.SUPPORT,
            weight=0.8,
            confidence=0.9,
            source="location_signal",
            explanation="Observed Tehran location evidence.",
        ),
        HypothesisObservation(
            target_value="karaj",
            polarity=ObservationPolarity.SUPPORT,
            weight=0.5,
            confidence=0.8,
            source="location_signal",
            explanation="Observed Karaj location evidence.",
        ),
    )

    assert definition.candidate_values(
        observations,
    ) == (
        "unknown",
        "karaj",
        "tehran",
    )


def test_open_set_candidate_values_remove_duplicates() -> None:
    definition = HypothesisDefinition(
        kind=HypothesisKind.LIKELY_LOCATION,
        allowed_values=("unknown",),
        unknown_value="unknown",
        allow_observed_values=True,
    )

    observations = (
        HypothesisObservation(
            target_value="tehran",
            polarity=ObservationPolarity.SUPPORT,
            weight=0.8,
            confidence=0.9,
            source="bio",
            explanation="Explicit Tehran location evidence.",
        ),
        HypothesisObservation(
            target_value="tehran",
            polarity=ObservationPolarity.SUPPORT,
            weight=0.6,
            confidence=0.8,
            source="geotag",
            explanation="Observed Tehran geotag.",
        ),
    )

    assert definition.candidate_values(
        observations,
    ) == (
        "unknown",
        "tehran",
    )


def test_open_set_candidate_values_are_order_invariant() -> None:
    definition = HypothesisDefinition(
        kind=HypothesisKind.LIKELY_LOCATION,
        allowed_values=("unknown",),
        unknown_value="unknown",
        allow_observed_values=True,
    )

    tehran = HypothesisObservation(
        target_value="tehran",
        polarity=ObservationPolarity.SUPPORT,
        weight=0.8,
        confidence=0.9,
        source="location_signal",
        explanation="Observed Tehran location evidence.",
    )

    karaj = HypothesisObservation(
        target_value="karaj",
        polarity=ObservationPolarity.SUPPORT,
        weight=0.5,
        confidence=0.8,
        source="location_signal",
        explanation="Observed Karaj location evidence.",
    )

    forward = definition.candidate_values(
        (
            tehran,
            karaj,
        )
    )

    reversed_order = definition.candidate_values(
        (
            karaj,
            tehran,
        )
    )

    assert forward == reversed_order

    assert forward == (
        "unknown",
        "karaj",
        "tehran",
    )
