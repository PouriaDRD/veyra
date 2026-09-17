"""Relationship intelligence value objects."""

from dataclasses import dataclass

from .enums import RelationshipSignalKind


@dataclass(frozen=True, slots=True)
class RelationshipSignal:
    """
    One contextual relationship-themed public signal.

    A signal does not establish relationship status.
    """

    kind: RelationshipSignalKind

    raw_value: str

    weight: float

    context: str | None = None

    def __post_init__(self) -> None:
        """Validate signal state."""

        raw_value = self.raw_value.strip()

        if not raw_value:
            raise ValueError(
                "raw_value must not be empty.",
            )

        if not 0 <= self.weight <= 1:
            raise ValueError(
                "weight must be between 0 and 1.",
            )

        context = self.context

        if context is not None:
            context = context.strip() or None

        object.__setattr__(
            self,
            "raw_value",
            raw_value,
        )

        object.__setattr__(
            self,
            "context",
            context,
        )
