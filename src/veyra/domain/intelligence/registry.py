"""Hypothesis strategy registry."""

from collections.abc import Iterable

from .enums import HypothesisKind
from .strategies import HypothesisStrategy


class HypothesisStrategyAlreadyRegisteredError(ValueError):
    """Raised when a strategy kind is registered more than once."""


class HypothesisStrategyNotFoundError(LookupError):
    """Raised when no strategy exists for a hypothesis kind."""


class HypothesisStrategyRegistry:
    """
    Registry of hypothesis strategies.

    Each ``HypothesisKind`` may have exactly one active strategy.

    Duplicate registration is rejected intentionally so configuration
    mistakes cannot silently replace inference behavior.
    """

    def __init__(
        self,
        strategies: Iterable[HypothesisStrategy] = (),
    ) -> None:
        self._strategies: dict[
            HypothesisKind,
            HypothesisStrategy,
        ] = {}

        for strategy in strategies:
            self.register(
                strategy,
            )

    def register(
        self,
        strategy: HypothesisStrategy,
    ) -> None:
        """Register one strategy."""

        self._validate_strategy(
            strategy,
        )

        kind = strategy.kind

        if kind in self._strategies:
            raise HypothesisStrategyAlreadyRegisteredError(
                f"hypothesis strategy already registered for kind: {kind.value}.",
            )

        self._strategies[kind] = strategy

    def get(
        self,
        kind: HypothesisKind,
    ) -> HypothesisStrategy:
        """Return the strategy registered for one kind."""

        try:
            return self._strategies[kind]

        except KeyError as exc:
            raise HypothesisStrategyNotFoundError(
                f"no hypothesis strategy registered for kind: {kind.value}.",
            ) from exc

    def contains(
        self,
        kind: HypothesisKind,
    ) -> bool:
        """Return whether one strategy kind is registered."""

        return kind in self._strategies

    @property
    def registered_kinds(
        self,
    ) -> tuple[HypothesisKind, ...]:
        """Return registered hypothesis kinds."""

        return tuple(self._strategies.keys())

    def _validate_strategy(
        self,
        strategy: HypothesisStrategy,
    ) -> None:
        """Validate strategy invariants before registration."""

        if not isinstance(
            strategy,
            HypothesisStrategy,
        ):
            raise TypeError(
                "strategy must implement HypothesisStrategy.",
            )

        if strategy.kind is not strategy.definition.kind:
            raise ValueError(
                "strategy kind must match definition kind.",
            )
