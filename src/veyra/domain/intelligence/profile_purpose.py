"""Profile-purpose intelligence signal models."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .enums import (
    ProfilePurpose,
    ProfilePurposeSignalKind,
)


@dataclass(frozen=True, slots=True)
class ProfilePurposeSignal:
    """
    One normalized profile-purpose signal.

    ``purpose`` represents the hypothesis candidate supported by this signal.

    ``weight`` represents semantic importance.

    ``confidence`` represents confidence that the source text was interpreted
    correctly.

    These values are semantic priors, not calibrated probabilities.
    """

    kind: ProfilePurposeSignalKind
    purpose: ProfilePurpose

    weight: float
    confidence: float

    raw_value: str

    context: str | None = None

    id: UUID = field(
        default_factory=uuid4,
    )

    def __post_init__(self) -> None:
        """Validate and normalize signal state."""

        raw_value = self.raw_value.strip()

        if not raw_value:
            raise ValueError(
                "profile-purpose signal raw_value must not be empty.",
            )

        if self.purpose is ProfilePurpose.UNKNOWN:
            raise ValueError(
                "profile-purpose signal must not target UNKNOWN.",
            )

        if not 0 <= self.weight <= 1:
            raise ValueError(
                "profile-purpose signal weight must be between 0 and 1.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "profile-purpose signal confidence must be between 0 and 1.",
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
