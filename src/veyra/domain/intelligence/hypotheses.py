"""Generic explainable hypothesis domain models."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from .enums import (
    HypothesisKind,
    HypothesisStatus,
)


class ObservationPolarity(StrEnum):
    """How an observation affects one candidate value."""

    SUPPORT = "support"
    OPPOSE = "oppose"


@dataclass(frozen=True, slots=True)
class HypothesisDefinition:
    """
    Definition of one generic multi-value hypothesis.

    Closed-set hypotheses only accept values listed in ``allowed_values``.

    Open-set hypotheses additionally accept normalized values discovered at
    runtime through observations. This is required for domains such as:

    - location
    - occupation
    - education
    - language
    - content interests

    The inference engine never needs to understand the semantic meaning of
    those values.
    """

    kind: HypothesisKind

    allowed_values: tuple[str, ...]

    unknown_value: str = "unknown"

    allow_observed_values: bool = False

    def __post_init__(self) -> None:
        """Validate and normalize hypothesis definition."""

        values = tuple(value.strip() for value in self.allowed_values)

        if not values:
            raise ValueError(
                "allowed_values must not be empty.",
            )

        if any(not value for value in values):
            raise ValueError(
                "allowed hypothesis values must not be empty.",
            )

        if len(
            set(
                values,
            )
        ) != len(values):
            raise ValueError(
                "allowed_values must be unique.",
            )

        unknown_value = self.unknown_value.strip()

        if not unknown_value:
            raise ValueError(
                "unknown_value must not be empty.",
            )

        if unknown_value not in values:
            raise ValueError(
                "unknown_value must exist in allowed_values.",
            )

        object.__setattr__(
            self,
            "allowed_values",
            values,
        )

        object.__setattr__(
            self,
            "unknown_value",
            unknown_value,
        )

    def accepts_value(
        self,
        value: str,
    ) -> bool:
        """Return whether one candidate value is valid for this definition."""

        normalized = value.strip()

        if not normalized:
            return False

        if normalized in self.allowed_values:
            return True

        return self.allow_observed_values

    def candidate_values(
        self,
        observations: tuple[
            "HypothesisObservation",
            ...,
        ],
    ) -> tuple[str, ...]:
        """
        Return deterministic candidate values for one evaluation.

        Closed-set definitions always return their static candidate list.

        Open-set definitions append normalized values discovered in
        observations. Runtime values are sorted so inference remains
        deterministic and independent from observation ordering.
        """

        if not self.allow_observed_values:
            return self.allowed_values

        discovered = sorted(
            {
                observation.target_value
                for observation in observations
                if (observation.target_value not in self.allowed_values)
            }
        )

        return (
            *self.allowed_values,
            *discovered,
        )


@dataclass(frozen=True, slots=True)
class HypothesisObservation:
    """
    One normalized observation used by the inference engine.

    ``weight``:
        Semantic importance of the observation.

    ``confidence``:
        Confidence that the observation itself was interpreted correctly.

    ``correlation_key``:
        Observations derived from the same underlying evidence/signal share
        one key. This prevents one source that fans out into several candidate
        observations from artificially inflating overall confidence.

    ``conflict_eligible``:
        Whether this observation may establish a real contradiction against
        another candidate.

        Broad contextual signals should normally set this to ``False``.
        Explicit mutually incompatible claims normally keep it ``True``.
    """

    target_value: str

    polarity: ObservationPolarity

    weight: float
    confidence: float

    source: str
    explanation: str

    correlation_key: str | None = None

    conflict_eligible: bool = True

    id: UUID = field(
        default_factory=uuid4,
    )

    def __post_init__(self) -> None:
        """Validate and normalize observation state."""

        target_value = self.target_value.strip()
        source = self.source.strip()
        explanation = self.explanation.strip()

        if not target_value:
            raise ValueError(
                "target_value must not be empty.",
            )

        if not source:
            raise ValueError(
                "source must not be empty.",
            )

        if not explanation:
            raise ValueError(
                "explanation must not be empty.",
            )

        if not 0 <= self.weight <= 1:
            raise ValueError(
                "weight must be between 0 and 1.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        correlation_key = self.correlation_key

        if correlation_key is not None:
            correlation_key = correlation_key.strip() or None

        object.__setattr__(
            self,
            "target_value",
            target_value,
        )

        object.__setattr__(
            self,
            "source",
            source,
        )

        object.__setattr__(
            self,
            "explanation",
            explanation,
        )

        object.__setattr__(
            self,
            "correlation_key",
            correlation_key,
        )

    @property
    def effective_strength(self) -> float:
        """Return semantic weight adjusted by observation confidence."""

        return round(
            self.weight * self.confidence,
            6,
        )


@dataclass(frozen=True, slots=True)
class HypothesisCandidateResult:
    """Explainable inference result for one possible value."""

    value: str

    score: float

    support: float
    opposition: float

    supporting_observations: tuple[
        HypothesisObservation,
        ...,
    ] = ()

    opposing_observations: tuple[
        HypothesisObservation,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        """Validate candidate result."""

        value = self.value.strip()

        if not value:
            raise ValueError(
                "value must not be empty.",
            )

        for field_name, number in (
            ("score", self.score),
            ("support", self.support),
            ("opposition", self.opposition),
        ):
            if not 0 <= number <= 1:
                raise ValueError(
                    f"{field_name} must be between 0 and 1.",
                )

        object.__setattr__(
            self,
            "value",
            value,
        )


@dataclass(frozen=True, slots=True)
class HypothesisResult:
    """
    Generic explainable inference result.

    Candidate scores are deterministic model scores and are not calibrated
    probabilities.

    Confidence describes how much independent usable evidence supports the
    inference process.
    """

    kind: HypothesisKind

    status: HypothesisStatus

    best_value: str

    confidence: float

    candidates: tuple[
        HypothesisCandidateResult,
        ...,
    ]

    algorithm_version: str

    def __post_init__(self) -> None:
        """Validate result state."""

        best_value = self.best_value.strip()
        algorithm_version = self.algorithm_version.strip()

        if not best_value:
            raise ValueError(
                "best_value must not be empty.",
            )

        if not algorithm_version:
            raise ValueError(
                "algorithm_version must not be empty.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        if not self.candidates:
            raise ValueError(
                "candidates must not be empty.",
            )

        candidate_values = {candidate.value for candidate in self.candidates}

        if best_value not in candidate_values:
            raise ValueError(
                "best_value must exist in candidates.",
            )

        object.__setattr__(
            self,
            "best_value",
            best_value,
        )

        object.__setattr__(
            self,
            "algorithm_version",
            algorithm_version,
        )

    def candidate_for(
        self,
        value: str,
    ) -> HypothesisCandidateResult | None:
        """Return one candidate result by normalized value."""

        for candidate in self.candidates:
            if candidate.value == value:
                return candidate

        return None
