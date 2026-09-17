"""Tests for application-level profile scoring orchestration."""

from datetime import date
from uuid import uuid4

import pytest

from veyra.application import ProfileAnalysisService
from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.application.scoring import (
    AnalysisScoringPolicy,
    EducationInstitutionScoringRule,
    FactValueScoringRule,
    ProfileScoringService,
)
from veyra.domain.evidence import FactKind
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def analyze(
    bio: str | None,
) -> ProfileAnalysisResult:
    """Analyze one deterministic eligible private adult profile."""

    profile_bio = "بانو" if bio is None else f"بانو | {bio}"

    return ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="scoring_service_1997",
            display_name=None,
            bio=profile_bio,
            is_private=True,
        ),
        reference_date=REFERENCE_DATE,
    )


def test_service_scores_matching_fact_end_to_end() -> None:
    result = ProfileScoringService().score(
        analyze(
            "Software Engineer",
        ),
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

    assert result.score == 10.0
    assert result.normalized_value == 1.0
    assert result.total_effective_weight == pytest.approx(
        1.92,
    )
    assert result.algorithm_version == "scoring-v1"
    assert result.is_scorable is True

    assert len(result.contributions) == 1

    contribution = result.contributions[0]

    assert contribution.key == "occupation-match"
    assert contribution.value == 1.0
    assert contribution.configured_weight == 2.0
    assert contribution.confidence == 0.96
    assert contribution.effective_weight == pytest.approx(
        1.92,
    )
    assert contribution.reason == "Desired occupation."


def test_service_scores_supported_mismatch_as_zero() -> None:
    result = ProfileScoringService().score(
        analyze(
            "Software Engineer",
        ),
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="occupation-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("doctor",),
                    weight=1.0,
                    reason="Desired occupation.",
                ),
            ),
        ),
    )

    assert result.score == 0.0
    assert result.normalized_value == 0.0
    assert result.is_scorable is True


def test_service_combines_multiple_weighted_features() -> None:
    result = ProfileScoringService().score(
        analyze(
            "Software Engineer | BSc Computer Science at MIT",
        ),
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
            relation_rules=(
                EducationInstitutionScoringRule(
                    key="education-pair",
                    education="bachelor:computer science",
                    institution="stanford university",
                    weight=1.0,
                    reason="Desired education pair.",
                ),
            ),
        ),
    )

    assert result.total_effective_weight == pytest.approx(
        2.89,
    )
    assert result.score == pytest.approx(
        6.643599,
    )

    assert tuple(contribution.key for contribution in result.contributions) == (
        "education-pair",
        "occupation-match",
    )


def test_service_returns_unscorable_result_for_empty_policy() -> None:
    result = ProfileScoringService().score(
        analyze(
            "Software Engineer",
        ),
        AnalysisScoringPolicy(),
    )

    assert result.score is None
    assert result.normalized_value is None
    assert result.total_effective_weight == 0.0
    assert result.contributions == ()
    assert result.algorithm_version == "scoring-v1"
    assert result.is_scorable is False


def test_service_returns_unscorable_when_configured_source_is_unknown() -> None:
    result = ProfileScoringService().score(
        analyze(
            None,
        ),
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

    assert result.score is None
    assert result.contributions == ()
    assert result.is_scorable is False


def test_service_returns_unscorable_for_gender_unknown_profile() -> None:
    analysis = ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="gender_unknown_1997",
            bio="Software Engineer",
            is_private=True,
        ),
        reference_date=REFERENCE_DATE,
    )

    result = ProfileScoringService().score(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="occupation-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("software engineer",),
                    weight=1.0,
                    reason="Desired occupation.",
                ),
            ),
        ),
    )

    assert result.score is None
    assert result.contributions == ()
    assert result.is_scorable is False
