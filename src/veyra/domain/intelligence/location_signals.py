"""Location intelligence signal models."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .enums import LocationSignalKind


@dataclass(frozen=True, slots=True)
class LocationSignal:
    """
    One normalized contextual or observed location signal.

    A location signal is intentionally not a fact.

    Examples:
    - a geotag on public content
    - a bare city mention in biography text
    - provider-reported public location metadata
    - a city mention in a public caption

    ``weight`` represents semantic importance.

    ``confidence`` represents confidence that the source was interpreted
    correctly.

    The generic hypothesis engine combines these values later.
    """

    kind: LocationSignalKind

    value: str

    weight: float
    confidence: float

    context: str | None = None

    id: UUID = field(
        default_factory=uuid4,
    )

    def __post_init__(self) -> None:
        """Validate and normalize signal state."""

        value = self.value.strip().casefold()

        if not value:
            raise ValueError(
                "location signal value must not be empty.",
            )

        if not 0 <= self.weight <= 1:
            raise ValueError(
                "location signal weight must be between 0 and 1.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "location signal confidence must be between 0 and 1.",
            )

        context = self.context

        if context is not None:
            context = context.strip() or None

        object.__setattr__(
            self,
            "value",
            value,
        )

        object.__setattr__(
            self,
            "context",
            context,
        )
