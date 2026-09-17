"""Tests for SearchService."""

import pytest

from veyra.application.dto import (
    AddCandidateCommand,
    CaptureSnapshotCommand,
    CreateProfileCommand,
    CreateSearchCommand,
)
from veyra.application.exceptions import CandidateAlreadyExistsError
from veyra.application.services import ProfileService, SearchService
from veyra.domain.profiles import Profile, SocialPlatform
from veyra.domain.searches import CandidateStatus, SearchCandidate, SearchStatus

from .fakes import FakeUnitOfWork


def build_candidate() -> tuple[
    FakeUnitOfWork,
    SearchService,
    Profile,
    SearchCandidate,
]:
    """Create one search candidate with its backing profile."""

    unit_of_work = FakeUnitOfWork()

    profile_service = ProfileService(
        unit_of_work,
    )
    search_service = SearchService(
        unit_of_work,
    )

    profile = profile_service.create(
        CreateProfileCommand(
            platform=SocialPlatform.INSTAGRAM,
            external_id="profile-1",
            username="candidate",
        )
    )

    search = search_service.create(
        CreateSearchCommand(
            platform=SocialPlatform.INSTAGRAM,
        )
    )

    candidate = search_service.add_candidate(
        AddCandidateCommand(
            search_id=search.id,
            profile_id=profile.id,
            discovery_source="test_provider",
        )
    )

    return (
        unit_of_work,
        search_service,
        profile,
        candidate,
    )


def test_search_service_creates_and_starts_search() -> None:
    unit_of_work = FakeUnitOfWork()

    service = SearchService(
        unit_of_work,
    )

    search = service.create(
        CreateSearchCommand(
            platform=SocialPlatform.INSTAGRAM,
        )
    )

    assert search.status is SearchStatus.CREATED

    started = service.start(
        search.id,
    )

    assert started.status is SearchStatus.DISCOVERING
    assert started.started_at is not None


def test_search_service_adds_candidate() -> None:
    _, _, _, candidate = build_candidate()

    assert candidate.status is CandidateStatus.DISCOVERED


def test_search_service_rejects_duplicate_candidate() -> None:
    _, search_service, profile, candidate = build_candidate()

    with pytest.raises(
        CandidateAlreadyExistsError,
    ):
        search_service.add_candidate(
            AddCandidateCommand(
                search_id=candidate.search_id,
                profile_id=profile.id,
                discovery_source="test_provider",
            )
        )


def test_search_service_snapshot_analysis_and_score_flow() -> None:
    (
        unit_of_work,
        search_service,
        profile,
        candidate,
    ) = build_candidate()

    snapshot = search_service.capture_snapshot(
        candidate.id,
        CaptureSnapshotCommand(
            profile_id=profile.id,
            username=profile.username,
            followers_count=120,
            following_count=80,
            posts_count=14,
            is_private=True,
        ),
    )

    stored_candidate = unit_of_work.candidates.get_by_id(
        candidate.id,
    )

    assert stored_candidate is not None
    assert stored_candidate.snapshot_id == snapshot.id
    assert stored_candidate.status is CandidateStatus.SNAPSHOTTED

    analyzed = search_service.mark_candidate_analyzed(
        candidate.id,
    )

    assert analyzed.status is CandidateStatus.ANALYZED

    scored = search_service.score_candidate(
        candidate.id,
        8.75,
    )

    assert scored.status is CandidateStatus.SCORED
    assert scored.score == 8.75


def test_public_profile_is_filtered_immediately_after_snapshot() -> None:
    (
        unit_of_work,
        search_service,
        profile,
        candidate,
    ) = build_candidate()

    search_service.capture_snapshot(
        candidate.id,
        CaptureSnapshotCommand(
            profile_id=profile.id,
            username=profile.username,
            is_private=False,
        ),
    )

    stored = unit_of_work.candidates.get_by_id(
        candidate.id,
    )

    assert stored is not None
    assert stored.status is CandidateStatus.FILTERED_OUT
    assert stored.score is None
    assert stored.exclusion_reason == ("Public profiles are not eligible for scoring.")


def test_unknown_privacy_cannot_receive_manual_score() -> None:
    (
        _,
        search_service,
        profile,
        candidate,
    ) = build_candidate()

    search_service.capture_snapshot(
        candidate.id,
        CaptureSnapshotCommand(
            profile_id=profile.id,
            username=profile.username,
            is_private=None,
        ),
    )

    search_service.mark_candidate_analyzed(
        candidate.id,
    )

    with pytest.raises(
        ValueError,
        match="privacy must be confirmed private",
    ):
        search_service.score_candidate(
            candidate.id,
            9.0,
        )
