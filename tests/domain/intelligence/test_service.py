"""Tests for generic hypothesis evaluation service."""

from veyra.domain.intelligence import (
    HypothesisDefinition,
    HypothesisEvaluationService,
    HypothesisKind,
    HypothesisObservation,
    HypothesisStatus,
    HypothesisStrategyRegistry,
    ObservationPolarity,
    StaticHypothesisStrategy,
)


def test_service_evaluates_registered_location_strategy() -> None:
    registry = HypothesisStrategyRegistry(
        (
            StaticHypothesisStrategy(
                definition=HypothesisDefinition(
                    kind=HypothesisKind.LIKELY_LOCATION,
                    allowed_values=(
                        "tehran",
                        "karaj",
                        "unknown",
                    ),
                )
            ),
        )
    )

    service = HypothesisEvaluationService(
        registry=registry,
    )

    result = service.evaluate(
        HypothesisKind.LIKELY_LOCATION,
        (
            HypothesisObservation(
                target_value="tehran",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.9,
                confidence=0.95,
                source="bio",
                explanation="Profile explicitly references Tehran.",
            ),
        ),
    )

    assert result.kind is HypothesisKind.LIKELY_LOCATION

    assert result.best_value == "tehran"

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_service_uses_same_engine_for_profile_purpose() -> None:
    registry = HypothesisStrategyRegistry(
        (
            StaticHypothesisStrategy(
                definition=HypothesisDefinition(
                    kind=HypothesisKind.PROFILE_PURPOSE,
                    allowed_values=(
                        "personal",
                        "professional",
                        "business",
                        "unknown",
                    ),
                )
            ),
        )
    )

    service = HypothesisEvaluationService(
        registry=registry,
    )

    result = service.evaluate(
        HypothesisKind.PROFILE_PURPOSE,
        (
            HypothesisObservation(
                target_value="professional",
                polarity=ObservationPolarity.SUPPORT,
                weight=0.8,
                confidence=0.9,
                source="bio",
                explanation="Professional title detected.",
            ),
        ),
    )

    assert result.kind is HypothesisKind.PROFILE_PURPOSE

    assert result.best_value == "professional"
