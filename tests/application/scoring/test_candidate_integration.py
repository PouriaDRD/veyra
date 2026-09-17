"""Tests for candidate scoring integration."""

from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest

from veyra.application import ProfileAnalysisService
from veyra.application.dto import (
    AddCandidateCommand,
    CaptureSnapshotCommand,
    CreateProfileCommand,
    CreateSearchCommand,
)
from veyra.application.scoring import (
    AnalysisScoringPolicy,
    FactValueScoringRule,
)
from veyra.application.services import ProfileService, SearchService
from veyra.domain.evidence import FactKind
from veyra.domain.profiles import SocialPlatform
from veyra.domain.searches import CandidateStatus, SearchCandidate
from veyra.domain.snapshots import ProfileSnapshot

from ..fakes import FakeUnitOfWork

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def build_analyzed_candidate(
    *,
    bio: str | None,
) -> tuple[
    FakeUnitOfWork,
    SearchService,
    SearchCandidate,
    ProfileSnapshot,
]:
    """Create one analyzed candidate and its captured snapshot."""

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
            external_id="candidate-scoring-profile",
            username="candidate_scoring_1997",
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

    snapshot = search_service.capture_snapshot(
        candidate.id,
        CaptureSnapshotCommand(
            profile_id=profile.id,
            username=profile.username,
            bio=bio,
        ),
    )

    search_service.mark_candidate_analyzed(
        candidate.id,
    )

    return (
        unit_of_work,
        search_service,
        candidate,
        snapshot,
    )


def test_score_candidate_from_analysis_persists_score_and_audit_snapshot() -> None:
    (
        unit_of_work,
        search_service,
        candidate,
        snapshot,
    ) = build_analyzed_candidate(
        bio="Software Engineer",
    )

    analysis = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    result = search_service.score_candidate_from_analysis(
        candidate.id,
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="occupation-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("software engineer",),
                    weight=2.0,
                    reason="Desired occupation.",
                ),
            ),
        ),
    )

    assert result.persisted is True
    assert result.candidate.status is CandidateStatus.SCORED
    assert result.candidate.score == 10.0

    assert result.score_result.score == 10.0
    assert len(result.score_result.contributions) == 1
    assert result.score_result.contributions[0].key == "occupation-match"

    assert result.audit_snapshot is not None
    assert result.audit_snapshot.candidate_id == candidate.id
    assert result.audit_snapshot.profile_snapshot_id == snapshot.id
    assert result.audit_snapshot.score == 10.0
    assert result.audit_snapshot.algorithm_version == "scoring-v1"
    assert result.audit_snapshot.contributions == result.score_result.contributions

    stored_candidate = unit_of_work.candidates.get_by_id(
        candidate.id,
    )

    assert stored_candidate is not None
    assert stored_candidate.status is CandidateStatus.SCORED
    assert stored_candidate.score == 10.0

    audit_history = unit_of_work.score_snapshots.list_for_candidate(
        candidate.id,
    )

    assert audit_history == [
        result.audit_snapshot,
    ]


def test_unscorable_result_does_not_persist_artificial_zero_or_audit() -> None:
    (
        unit_of_work,
        search_service,
        candidate,
        snapshot,
    ) = build_analyzed_candidate(
        bio=None,
    )

    analysis = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    result = search_service.score_candidate_from_analysis(
        candidate.id,
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="employer-match",
                    kind=FactKind.EMPLOYER,
                    accepted_values=("openai",),
                    weight=1.0,
                    reason="Desired employer.",
                ),
            ),
        ),
    )

    assert result.persisted is False
    assert result.score_result.score is None
    assert result.audit_snapshot is None
    assert result.candidate.status is CandidateStatus.ANALYZED
    assert result.candidate.score is None

    stored = unit_of_work.candidates.get_by_id(
        candidate.id,
    )

    assert stored is not None
    assert stored.status is CandidateStatus.ANALYZED
    assert stored.score is None
    assert unit_of_work.score_snapshots.list_for_candidate(candidate.id) == []


def test_candidate_scoring_rejects_analysis_for_different_profile() -> None:
    (
        _,
        search_service,
        candidate,
        snapshot,
    ) = build_analyzed_candidate(
        bio="Software Engineer",
    )

    analysis = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    wrong_analysis = replace(
        analysis,
        profile_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="Analysis profile does not match candidate profile",
    ):
        search_service.score_candidate_from_analysis(
            candidate.id,
            wrong_analysis,
            AnalysisScoringPolicy(),
        )


def test_candidate_scoring_rejects_analysis_for_different_snapshot() -> None:
    (
        _,
        search_service,
        candidate,
        snapshot,
    ) = build_analyzed_candidate(
        bio="Software Engineer",
    )

    analysis = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    wrong_analysis = replace(
        analysis,
        snapshot_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="Analysis snapshot does not match candidate snapshot",
    ):
        search_service.score_candidate_from_analysis(
            candidate.id,
            wrong_analysis,
            AnalysisScoringPolicy(),
        )
