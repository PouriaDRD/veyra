"""Evidence and normalized fact domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now

from .enums import (
    ConfidenceLevel,
    EvidenceSource,
    FactKind,
    FactStatus,
)

type FactValue = str | int | float | bool


@dataclass(frozen=True, slots=True)
class Evidence:
    """
    One explainable observation supporting a normalized fact.

    Evidence contains only explicit/publicly observable information.
    """

    source: EvidenceSource
    raw_value: str
    normalized_value: FactValue
    confidence: float

    id: UUID = field(
        default_factory=uuid4,
    )

    observed_at: datetime = field(
        default_factory=utc_now,
    )

    extractor: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize evidence."""

        raw_value = self.raw_value.strip()

        if not raw_value:
            raise ValueError(
                "raw_value must not be empty.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        extractor = self.extractor

        if extractor is not None:
            extractor = extractor.strip() or None

        object.__setattr__(
            self,
            "raw_value",
            raw_value,
        )

        object.__setattr__(
            self,
            "extractor",
            extractor,
        )

        object.__setattr__(
            self,
            "observed_at",
            ensure_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class Fact:
    """
    Resolved normalized fact derived from one or more evidence items.

    Facts remain explainable because supporting evidence is retained.
    """

    kind: FactKind
    status: FactStatus
    confidence: float

    value: FactValue | None = None

    evidence: tuple[Evidence, ...] = ()

    id: UUID = field(
        default_factory=uuid4,
    )

    resolved_at: datetime = field(
        default_factory=utc_now,
    )

    def __post_init__(self) -> None:
        """Validate normalized fact invariants."""

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        if self.status is FactStatus.UNKNOWN:
            if self.value is not None:
                raise ValueError(
                    "unknown fact must not have a value.",
                )

            if self.evidence:
                raise ValueError(
                    "unknown fact must not contain evidence.",
                )

            if self.confidence != 0:
                raise ValueError(
                    "unknown fact confidence must be zero.",
                )

        elif self.status is FactStatus.SUPPORTED:
            if self.value is None:
                raise ValueError(
                    "supported fact must have a value.",
                )

            if not self.evidence:
                raise ValueError(
                    "supported fact must contain evidence.",
                )

        elif self.status is FactStatus.CONFLICTED:
            if self.value is not None:
                raise ValueError(
                    "conflicted fact must not have a resolved value.",
                )

            if len(self.evidence) < 2:
                raise ValueError(
                    "conflicted fact must contain at least two evidence items.",
                )

        object.__setattr__(
            self,
            "resolved_at",
            ensure_utc_datetime(
                self.resolved_at,
                field_name="resolved_at",
            ),
        )

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Return the qualitative confidence band."""

        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW

        if self.confidence < 0.4:
            return ConfidenceLevel.LOW

        if self.confidence < 0.6:
            return ConfidenceLevel.MEDIUM

        if self.confidence < 0.8:
            return ConfidenceLevel.HIGH

        return ConfidenceLevel.VERY_HIGH
