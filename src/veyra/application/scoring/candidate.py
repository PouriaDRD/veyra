"""Candidate scoring application result models."""

from dataclasses import dataclass

from veyra.domain.scoring import ScoreResult
from veyra.domain.searches import SearchCandidate


@dataclass(frozen=True, slots=True)
class CandidateScoringResult:
    """
    Result of attempting to score and persist one search candidate.

    ``score_result`` retains the full explainable score breakdown while the
    candidate persists only its normalized numeric score.
    """

    candidate: SearchCandidate
    score_result: ScoreResult
    persisted: bool

    def __post_init__(self) -> None:
        """Validate persistence/result consistency."""

        if self.persisted:
            if self.score_result.score is None:
                raise ValueError(
                    "persisted scoring result must contain a score.",
                )

            if self.candidate.score != self.score_result.score:
                raise ValueError(
                    "candidate score must match persisted score result.",
                )
            return

        if self.score_result.score is not None:
            raise ValueError(
                "non-persisted scoring result must be unscorable.",
            )
