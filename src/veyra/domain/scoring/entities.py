"""Scoring domain value objects."""

from dataclasses import dataclass

from .enums import ScoringSourceKind


def _validate_unit_interval(
    value: float,
    *,
    field_name: str,
) -> float:
    """Validate and normalize a numeric value in the inclusive 0-1 range."""

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a numeric value between 0 and 1.",
        )

    normalized = float(value)

    if not 0 <= normalized <= 1:
        raise ValueError(
            f"{field_name} must be between 0 and 1.",
        )

    return normalized


@dataclass(frozen=True, slots=True)
class ScoringFeature:
    """
    One normalized feature prepared for scoring.

    ``value`` expresses how strongly the feature satisfies its scoring rule.
    ``confidence`` controls how much influence that value receives.
    ``weight`` expresses configured business importance.
    """

    key: str
    value: float
    weight: float
    confidence: float
    reason: str
    source_kind: ScoringSourceKind
    source_key: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate feature invariants."""

        key = self.key.strip()
        reason = self.reason.strip()

        if not key:
            raise ValueError(
                "key must not be empty.",
            )

        if not reason:
            raise ValueError(
                "reason must not be empty.",
            )

        if isinstance(self.weight, bool):
            raise ValueError(
                "weight must be a non-negative numeric value.",
            )

        weight = float(
            self.weight,
        )

        if weight < 0:
            raise ValueError(
                "weight must be non-negative.",
            )

        source_key = self.source_key
        if source_key is not None:
            source_key = source_key.strip() or None

        object.__setattr__(
            self,
            "key",
            key,
        )
        object.__setattr__(
            self,
            "value",
            _validate_unit_interval(
                self.value,
                field_name="value",
            ),
        )
        object.__setattr__(
            self,
            "weight",
            weight,
        )
        object.__setattr__(
            self,
            "confidence",
            _validate_unit_interval(
                self.confidence,
                field_name="confidence",
            ),
        )
        object.__setattr__(
            self,
            "reason",
            reason,
        )
        object.__setattr__(
            self,
            "source_key",
            source_key,
        )

    @property
    def effective_weight(self) -> float:
        """Return confidence-adjusted feature weight."""

        return self.weight * self.confidence

    @property
    def weighted_value(self) -> float:
        """Return this feature's weighted contribution before normalization."""

        return self.value * self.effective_weight


@dataclass(frozen=True, slots=True)
class ScoreContribution:
    """Explainable contribution of one feature to a score result."""

    key: str
    value: float
    configured_weight: float
    confidence: float
    effective_weight: float
    weighted_value: float
    reason: str
    source_kind: ScoringSourceKind
    source_key: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """
    Explainable normalized scoring result.

    ``score`` is ``None`` when no feature carries positive effective weight.
    This distinguishes "not enough scorable information" from a real score of
    zero.
    """

    score: float | None
    normalized_value: float | None
    total_effective_weight: float
    contributions: tuple[ScoreContribution, ...]
    algorithm_version: str

    @property
    def is_scorable(self) -> bool:
        """Return whether the result contains enough weighted information."""

        return self.score is not None
