"""Tests for SearchCandidate domain behavior."""

from uuid import uuid4

import pytest

from veyra.domain.searches import (
    CandidateStatus,
    SearchCandidate,
)


def build_candidate() -> SearchCandidate:
    """Create a candidate for tests."""

    return SearchCandidate(
        search_id=uuid4(),
        profile_id=uuid4(),
        discovery_source="instagram_public_source",
    )


def test_candidate_starts_discovered() -> None:
    candidate = build_candidate()

    assert candidate.status is CandidateStatus.DISCOVERED
    assert candidate.snapshot_id is None
    assert candidate.score is None


def test_candidate_can_be_scored_after_analysis() -> None:
    candidate = build_candidate()

    candidate.attach_snapshot(
        uuid4(),
    )

    candidate.mark_analyzed()

    candidate.set_score(
        8.75,
    )

    assert candidate.status is CandidateStatus.SCORED
    assert candidate.score == 8.75


def test_candidate_can_be_filtered_out() -> None:
    candidate = build_candidate()

    candidate.attach_snapshot(
        uuid4(),
    )

    candidate.mark_analyzed()

    candidate.filter_out(
        "Does not satisfy search rules.",
    )

    assert candidate.status is CandidateStatus.FILTERED_OUT

    assert candidate.exclusion_reason == ("Does not satisfy search rules.")

    assert candidate.score is None


def test_candidate_rejects_invalid_score() -> None:
    candidate = build_candidate()

    candidate.attach_snapshot(
        uuid4(),
    )

    candidate.mark_analyzed()

    with pytest.raises(
        ValueError,
        match="score must be between 0 and 10",
    ):
        candidate.set_score(
            11,
        )


def test_scored_candidate_requires_snapshot() -> None:
    with pytest.raises(
        ValueError,
        match="processed candidate must have snapshot_id",
    ):
        SearchCandidate(
            search_id=uuid4(),
            profile_id=uuid4(),
            discovery_source="test",
            status=CandidateStatus.SCORED,
            score=8.0,
        )


def test_boolean_score_is_rejected() -> None:
    candidate = build_candidate()

    candidate.attach_snapshot(
        uuid4(),
    )

    candidate.mark_analyzed()

    with pytest.raises(
        ValueError,
        match="score must be a numeric value",
    ):
        candidate.set_score(
            True,
        )
