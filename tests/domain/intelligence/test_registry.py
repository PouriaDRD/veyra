"""Tests for the hypothesis strategy registry."""

import pytest

from veyra.domain.intelligence import (
    HypothesisDefinition,
    HypothesisKind,
    HypothesisStrategyAlreadyRegisteredError,
    HypothesisStrategyNotFoundError,
    HypothesisStrategyRegistry,
    StaticHypothesisStrategy,
)


def build_strategy(
    kind: HypothesisKind,
    values: tuple[str, ...],
) -> StaticHypothesisStrategy:
    """Create one generic strategy."""

    return StaticHypothesisStrategy(
        definition=HypothesisDefinition(
            kind=kind,
            allowed_values=values,
        )
    )


def test_registry_registers_strategy() -> None:
    registry = HypothesisStrategyRegistry()

    strategy = build_strategy(
        HypothesisKind.LIKELY_LOCATION,
        (
            "tehran",
            "karaj",
            "unknown",
        ),
    )

    registry.register(
        strategy,
    )

    assert registry.contains(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert registry.get(HypothesisKind.LIKELY_LOCATION) is strategy


def test_registry_accepts_initial_strategies() -> None:
    location = build_strategy(
        HypothesisKind.LIKELY_LOCATION,
        (
            "tehran",
            "unknown",
        ),
    )

    purpose = build_strategy(
        HypothesisKind.PROFILE_PURPOSE,
        (
            "personal",
            "professional",
            "unknown",
        ),
    )

    registry = HypothesisStrategyRegistry(
        (
            location,
            purpose,
        )
    )

    assert registry.registered_kinds == (
        HypothesisKind.LIKELY_LOCATION,
        HypothesisKind.PROFILE_PURPOSE,
    )


def test_registry_rejects_duplicate_strategy_kind() -> None:
    registry = HypothesisStrategyRegistry()

    first = build_strategy(
        HypothesisKind.LIKELY_LOCATION,
        (
            "tehran",
            "unknown",
        ),
    )

    second = build_strategy(
        HypothesisKind.LIKELY_LOCATION,
        (
            "london",
            "unknown",
        ),
    )

    registry.register(
        first,
    )

    with pytest.raises(
        HypothesisStrategyAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            second,
        )


def test_registry_raises_for_unknown_strategy() -> None:
    registry = HypothesisStrategyRegistry()

    with pytest.raises(
        HypothesisStrategyNotFoundError,
        match="no hypothesis strategy registered",
    ):
        registry.get(
            HypothesisKind.ACTIVITY_LEVEL,
        )


def test_registered_kinds_preserve_registration_order() -> None:
    registry = HypothesisStrategyRegistry()

    registry.register(
        build_strategy(
            HypothesisKind.PROFILE_PURPOSE,
            (
                "personal",
                "unknown",
            ),
        )
    )

    registry.register(
        build_strategy(
            HypothesisKind.ACTIVITY_LEVEL,
            (
                "low",
                "high",
                "unknown",
            ),
        )
    )

    assert registry.registered_kinds == (
        HypothesisKind.PROFILE_PURPOSE,
        HypothesisKind.ACTIVITY_LEVEL,
    )
