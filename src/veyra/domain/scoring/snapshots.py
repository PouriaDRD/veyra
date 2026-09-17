"""Immutable audit snapshots for completed scoring runs."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now

from .entities import ScoreContribution, ScoreResult


@dataclass(frozen=True, slots=True)
class ScoreSnapshot:
    """
    Immutable audit record for one completed candidate scoring run.

    The snapshot captures the numeric result, algorithm version, and full
    explainability contributions independently from the mutable candidate.
    """

    candidate_id: UUID
    profile_snapshot_id: UUID
    score: float
    normalized_value: float
    total_effective_weight: float
    contributions: tuple[ScoreContribution, ...]
    algorithm_version: str

    id: UUID = field(
        default_factory=uuid4,
    )

    created_at: datetime = field(
        default_factory=utc_now,
    )

    def __post_init__(self) -> None:
        """Validate immutable audit snapshot invariants."""

        if not 0 <= self.score <= 10:
            raise ValueError(
                "score must be between 0 and 10.",
            )

        if not 0 <= self.normalized_value <= 1:
            raise ValueError(
                "normalized_value must be between 0 and 1.",
            )

        if self.total_effective_weight <= 0:
            raise ValueError(
                "total_effective_weight must be greater than zero.",
            )

        algorithm_version = self.algorithm_version.strip()

        if not algorithm_version:
            raise ValueError(
                "algorithm_version must not be empty.",
            )

        if not self.contributions:
            raise ValueError(
                "score snapshot must contain contributions.",
            )

        object.__setattr__(
            self,
            "algorithm_version",
            algorithm_version,
        )
        object.__setattr__(
            self,
            "created_at",
            ensure_utc_datetime(
                self.created_at,
                field_name="created_at",
            ),
        )

    @classmethod
    def from_result(
        cls,
        *,
        candidate_id: UUID,
        profile_snapshot_id: UUID,
        result: ScoreResult,
    ) -> "ScoreSnapshot":
        """Create an audit snapshot from one scorable result."""

        if result.score is None or result.normalized_value is None:
            raise ValueError(
                "cannot create score snapshot from unscorable result.",
            )

        return cls(
            candidate_id=candidate_id,
            profile_snapshot_id=profile_snapshot_id,
            score=result.score,
            normalized_value=result.normalized_value,
            total_effective_weight=result.total_effective_weight,
            contributions=result.contributions,
            algorithm_version=result.algorithm_version,
        )
