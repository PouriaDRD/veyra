"""Tests for generic hypothesis strategies."""

from veyra.domain.intelligence import (
    HypothesisDefinition,
    HypothesisKind,
    HypothesisObservation,
    ObservationPolarity,
    StaticHypothesisStrategy,
)


def build_strategy() -> StaticHypothesisStrategy:
    """Create a generic profile-purpose strategy."""

    return StaticHypothesisStrategy(
        definition=HypothesisDefinition(
            kind=HypothesisKind.PROFILE_PURPOSE,
            allowed_values=(
                "personal",
                "professional",
                "business",
                "unknown",
            ),
        )
    )


def test_static_strategy_exposes_definition_kind() -> None:
    strategy = build_strategy()

    assert strategy.kind is HypothesisKind.PROFILE_PURPOSE


def test_static_strategy_preserves_observations() -> None:
    strategy = build_strategy()

    observation = HypothesisObservation(
        target_value="professional",
        polarity=ObservationPolarity.SUPPORT,
        weight=0.8,
        confidence=0.9,
        source="bio",
        explanation="Professional title found.",
    )

    prepared = strategy.prepare_observations((observation,))

    assert prepared == (observation,)
