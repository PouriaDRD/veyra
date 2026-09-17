"""Candidate scoring application result models."""

from dataclasses import dataclass

from veyra.domain.scoring import ScoreResult, ScoreSnapshot
from veyra.domain.searches import SearchCandidate


@dataclass(frozen=True, slots=True)
class CandidateScoringResult:
    """
    Result of attempting to score and persist one search candidate.

    Successful scoring returns both the explainable score result and the
    immutable audit snapshot persisted in the same transaction.
    """

    candidate: SearchCandidate
    score_result: ScoreResult
    persisted: bool
    audit_snapshot: ScoreSnapshot | None = None

    def __post_init__(self) -> None:
        """Validate candidate, result, and audit persistence consistency."""

        if self.persisted:
            if self.score_result.score is None:
                raise ValueError(
                    "persisted scoring result must contain a score.",
                )

            if self.candidate.score != self.score_result.score:
                raise ValueError(
                    "candidate score must match persisted score result.",
                )

            if self.audit_snapshot is None:
                raise ValueError(
                    "persisted scoring result must contain an audit snapshot.",
                )

            if self.audit_snapshot.candidate_id != self.candidate.id:
                raise ValueError(
                    "audit snapshot candidate must match scored candidate.",
                )

            if self.audit_snapshot.profile_snapshot_id != self.candidate.snapshot_id:
                raise ValueError(
                    "audit snapshot profile snapshot must match candidate snapshot.",
                )

            if self.audit_snapshot.score != self.score_result.score:
                raise ValueError(
                    "audit snapshot score must match score result.",
                )

            return

        if self.score_result.score is not None:
            raise ValueError(
                "non-persisted scoring result must be unscorable.",
            )

        if self.audit_snapshot is not None:
            raise ValueError(
                "non-persisted scoring result must not contain an audit snapshot.",
            )
