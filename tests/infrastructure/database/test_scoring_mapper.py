"""Tests for scoring audit persistence mapping."""

from uuid import uuid4

from veyra.domain.scoring import (
    ScoreContribution,
    ScoreSnapshot,
    ScoringSourceKind,
)
from veyra.infrastructure.database.mappers import (
    score_snapshot_to_domain,
    score_snapshot_to_model,
)


def test_score_snapshot_mapper_round_trips_explainability() -> None:
    snapshot = ScoreSnapshot(
        candidate_id=uuid4(),
        profile_snapshot_id=uuid4(),
        score=7.5,
        normalized_value=0.75,
        total_effective_weight=1.6,
        contributions=(
            ScoreContribution(
                key="education-match",
                value=0.75,
                configured_weight=2.0,
                confidence=0.8,
                effective_weight=1.6,
                weighted_value=1.2,
                reason="Desired education.",
                source_kind=ScoringSourceKind.FACT,
                source_key="fact:education",
            ),
        ),
        algorithm_version="scoring-v1",
    )

    restored = score_snapshot_to_domain(
        score_snapshot_to_model(
            snapshot,
        )
    )

    assert restored == snapshot
