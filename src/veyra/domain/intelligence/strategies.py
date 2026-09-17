"""Generic hypothesis strategy contracts."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .enums import HypothesisKind
from .hypotheses import (
    HypothesisDefinition,
    HypothesisObservation,
)


@runtime_checkable
class HypothesisStrategy(Protocol):
    """
    Contract implemented by one hypothesis-domain strategy.

    A strategy defines:
    - which hypothesis kind it owns
    - which candidate values are valid
    - how already-normalized observations should be prepared before
      evaluation

    Raw profile parsing remains outside this contract. Extractors and
    adapters convert multilingual/public profile data into generic
    ``HypothesisObservation`` objects first.
    """

    @property
    def kind(self) -> HypothesisKind:
        """Return the hypothesis kind handled by this strategy."""

        ...

    @property
    def definition(self) -> HypothesisDefinition:
        """Return the strategy's hypothesis definition."""

        ...

    def prepare_observations(
        self,
        observations: Iterable[HypothesisObservation],
    ) -> tuple[HypothesisObservation, ...]:
        """Prepare observations before generic engine evaluation."""

        ...


@dataclass(frozen=True, slots=True)
class StaticHypothesisStrategy:
    """
    Basic strategy backed by a static hypothesis definition.

    This is sufficient for hypotheses that only need a fixed candidate
    vocabulary and do not require additional observation transformation.
    """

    definition: HypothesisDefinition

    def __post_init__(self) -> None:
        """Validate strategy definition."""

        if not self.definition.allowed_values:
            raise ValueError(
                "strategy definition must contain allowed values.",
            )

    @property
    def kind(self) -> HypothesisKind:
        """Return the hypothesis kind handled by this strategy."""

        return self.definition.kind

    def prepare_observations(
        self,
        observations: Iterable[HypothesisObservation],
    ) -> tuple[HypothesisObservation, ...]:
        """
        Preserve normalized observations unchanged.

        Domain-specific strategies may override this behavior later.
        """

        return tuple(observations)
