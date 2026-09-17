"""Evidence and normalized fact domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
)

from .birth_year import BirthYear
from .cardinality import fact_cardinality_for
from .enums import (
    ConfidenceLevel,
    EvidenceSource,
    FactCardinality,
    FactKind,
    FactStatus,
)

type FactValue = str | int | float | bool | BirthYear


@dataclass(frozen=True, slots=True)
class Evidence:
    """
    One explainable observation supporting a normalized fact.

    Evidence contains only explicit or publicly observable information.

    ``nature`` describes what kind of evidence this is.
    ``strength`` describes its semantic strength.
    ``confidence`` remains the numeric confidence assigned to the specific
    normalized interpretation.

    Ambiguous evidence represents one possible interpretation of a raw
    observation rather than a definitive contradictory claim.
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

    nature: EvidenceNature = EvidenceNature.OBSERVED

    strength: EvidenceStrength = EvidenceStrength.MODERATE

    is_ambiguous: bool = False

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

        if self.is_ambiguous and self.nature is not EvidenceNature.AMBIGUOUS:
            object.__setattr__(
                self,
                "nature",
                EvidenceNature.AMBIGUOUS,
            )

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

    Scalar facts expose their resolved value through ``value``.
    Multi-value facts expose their resolved values through ``values``.

    Facts remain explainable because supporting evidence is retained.
    """

    kind: FactKind
    status: FactStatus
    confidence: float

    value: FactValue | None = None

    values: tuple[FactValue, ...] = ()

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

        cardinality = fact_cardinality_for(
            self.kind,
        )

        if self.status is FactStatus.UNKNOWN:
            if self.value is not None:
                raise ValueError(
                    "unknown fact must not have a value.",
                )

            if self.values:
                raise ValueError(
                    "unknown fact must not have values.",
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
            if cardinality is FactCardinality.SINGLE:
                if self.value is None:
                    raise ValueError(
                        "supported scalar fact must have a value.",
                    )

                if self.values:
                    raise ValueError(
                        "supported scalar fact must not have multiple values.",
                    )

            else:
                if self.value is not None:
                    raise ValueError(
                        "supported multi-value fact must not have a scalar value.",
                    )

                if not self.values:
                    raise ValueError(
                        "supported multi-value fact must contain values.",
                    )

                if len(set(self.values)) != len(self.values):
                    raise ValueError(
                        "supported multi-value fact values must be unique.",
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

            if self.values:
                raise ValueError(
                    "conflicted fact must not have resolved values.",
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
    def cardinality(self) -> FactCardinality:
        """Return this fact kind's cardinality policy."""

        return fact_cardinality_for(
            self.kind,
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
