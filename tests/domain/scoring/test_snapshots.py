"""Tests for immutable score audit snapshots."""

from uuid import uuid4

import pytest

from veyra.domain.scoring import (
    ScoreContribution,
    ScoreResult,
    ScoreSnapshot,
    ScoringSourceKind,
)


def contribution() -> ScoreContribution:
    """Build one deterministic contribution."""

    return ScoreContribution(
        key="occupation-match",
        value=1.0,
        configured_weight=2.0,
        confidence=0.96,
        effective_weight=1.92,
        weighted_value=1.92,
        reason="Desired occupation.",
        source_kind=ScoringSourceKind.FACT,
        source_key="fact:occupation",
    )


def result() -> ScoreResult:
    """Build one scorable result."""

    return ScoreResult(
        score=10.0,
        normalized_value=1.0,
        total_effective_weight=1.92,
        contributions=(contribution(),),
        algorithm_version="scoring-v1",
    )


def test_score_snapshot_is_created_from_scorable_result() -> None:
    candidate_id = uuid4()
    profile_snapshot_id = uuid4()

    snapshot = ScoreSnapshot.from_result(
        candidate_id=candidate_id,
        profile_snapshot_id=profile_snapshot_id,
        result=result(),
    )

    assert snapshot.candidate_id == candidate_id
    assert snapshot.profile_snapshot_id == profile_snapshot_id
    assert snapshot.score == 10.0
    assert snapshot.normalized_value == 1.0
    assert snapshot.total_effective_weight == 1.92
    assert snapshot.algorithm_version == "scoring-v1"
    assert snapshot.contributions == (contribution(),)


def test_score_snapshot_rejects_unscorable_result() -> None:
    with pytest.raises(
        ValueError,
        match="cannot create score snapshot from unscorable result",
    ):
        ScoreSnapshot.from_result(
            candidate_id=uuid4(),
            profile_snapshot_id=uuid4(),
            result=ScoreResult(
                score=None,
                normalized_value=None,
                total_effective_weight=0.0,
                contributions=(),
                algorithm_version="scoring-v1",
            ),
        )


@pytest.mark.parametrize(
    ("score", "normalized_value"),
    (
        (-0.1, 0.0),
        (10.1, 1.0),
        (0.0, -0.1),
        (10.0, 1.1),
    ),
)
def test_score_snapshot_validates_normalized_ranges(
    score: float,
    normalized_value: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        ScoreSnapshot(
            candidate_id=uuid4(),
            profile_snapshot_id=uuid4(),
            score=score,
            normalized_value=normalized_value,
            total_effective_weight=1.0,
            contributions=(contribution(),),
            algorithm_version="scoring-v1",
        )
