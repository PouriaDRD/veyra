"""General profile-intelligence value objects."""

from dataclasses import dataclass

from .enums import (
    HypothesisKind,
    HypothesisStatus,
)


@dataclass(frozen=True, slots=True)
class HypothesisScore:
    """
    One explainable derived hypothesis.

    ``probability`` expresses the model's current estimated likelihood.

    ``confidence`` expresses how trustworthy that probability estimate is,
    based on evidence quantity, quality, agreement, and calibration.
    """

    kind: HypothesisKind
    value: str

    probability: float
    confidence: float

    status: HypothesisStatus

    evidence_count: int = 0

    def __post_init__(self) -> None:
        """Validate hypothesis state."""

        value = self.value.strip()

        if not value:
            raise ValueError(
                "value must not be empty.",
            )

        if not 0 <= self.probability <= 1:
            raise ValueError(
                "probability must be between 0 and 1.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        if self.evidence_count < 0:
            raise ValueError(
                "evidence_count must not be negative.",
            )

        object.__setattr__(
            self,
            "value",
            value,
        )
