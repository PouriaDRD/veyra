"""Generic hypothesis evaluation service."""

from collections.abc import Iterable

from .engine import HypothesisEngine
from .enums import HypothesisKind
from .hypotheses import (
    HypothesisObservation,
    HypothesisResult,
)
from .registry import HypothesisStrategyRegistry


class HypothesisEvaluationService:
    """
    Evaluate registered hypothesis strategies through the generic engine.

    This service remains domain-agnostic. Relationship, location, activity,
    occupation, profile-purpose, and future domains all use the same flow.
    """

    def __init__(
        self,
        *,
        registry: HypothesisStrategyRegistry,
        engine: HypothesisEngine | None = None,
    ) -> None:
        self._registry = registry

        self._engine = engine if engine is not None else HypothesisEngine()

    def evaluate(
        self,
        kind: HypothesisKind,
        observations: Iterable[HypothesisObservation],
    ) -> HypothesisResult:
        """Evaluate observations for one registered hypothesis kind."""

        strategy = self._registry.get(
            kind,
        )

        prepared = strategy.prepare_observations(
            observations,
        )

        return self._engine.evaluate(
            strategy.definition,
            prepared,
        )
