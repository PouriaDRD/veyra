"""Location intelligence signal models."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .enums import (
    LocationRelation,
    LocationSignalKind,
)


@dataclass(frozen=True, slots=True)
class LocationSignal:
    """
    One normalized contextual or observed location signal.

    A location signal is intentionally not a fact.

    ``kind`` describes where the signal came from.

    ``relation`` describes what the geographic entity means relative to the
    profile. Source and semantic relation must remain independent.

    Examples:
    - BIO_MENTION + ORIGIN
    - BIO_MENTION + CONTEXTUAL_MENTION
    - GEOTAG + CONTENT_LOCATION
    - PROFILE_METADATA + CURRENT_RESIDENCE

    ``weight`` represents semantic importance.

    ``confidence`` represents confidence that the source was interpreted
    correctly.
    """

    kind: LocationSignalKind
    value: str

    weight: float
    confidence: float

    relation: LocationRelation = LocationRelation.UNSPECIFIED

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
