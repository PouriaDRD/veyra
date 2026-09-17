"""End-to-end tests for profile-purpose analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisStatus,
    ProfilePurpose,
)
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def build_snapshot(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> ProfileSnapshot:
    """Create one deterministic adult-profile analysis fixture."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="purpose_test_1997",
        display_name=display_name,
        bio=bio,
    )


def test_professional_bio_produces_professional_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | Python",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value

    assert hypothesis.status is HypothesisStatus.PROBABLE


def test_persian_professional_bio_is_supported() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="مهندس نرم افزار | پایتون",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value

    assert hypothesis.status is HypothesisStatus.PROBABLE


def test_creator_bio_produces_creator_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Content Creator | YouTuber",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_creator_bio_is_supported() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="تولید محتوا | بلاگر",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_business_bio_produces_business_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Online Shop | DM for order",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_business_bio_is_supported() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="فروشگاه | ثبت سفارش",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_organization_bio_produces_organization_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Nonprofit Foundation",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.ORGANIZATION.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_personal_profile_marker_is_supported() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Personal account | my life",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.PERSONAL.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_display_name_can_supply_profile_purpose_signal() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            display_name="Content Creator",
            bio="Coffee | Tehran",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_unrelated_profile_text_returns_unknown_purpose() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            display_name="Sara",
            bio="Coffee | Tehran | Music",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_business_signal_outweighs_professional_signal() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | Online Shop",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value


def test_creator_and_business_can_remain_ambiguous() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Content Creator | Online Shop",
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    assert hypothesis.status is HypothesisStatus.AMBIGUOUS

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_relationship_location_and_purpose_hypotheses_coexist() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio=("متاهل | ساکن تهران | مهندس نرم افزار"),
        ),
        reference_date=REFERENCE_DATE,
    )

    relationship = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    location = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    purpose = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert relationship is not None
    assert location is not None
    assert purpose is not None

    assert relationship.best_value == "married"
    assert location.best_value == "tehran"

    assert purpose.best_value == ProfilePurpose.PROFESSIONAL.value


def test_bio_purpose_observations_share_one_correlation_group() -> None:
    snapshot = build_snapshot(
        bio="Designer | Content Creator",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    observations = tuple(
        observation
        for observation in result.observations
        if observation.source.startswith("profile_purpose_signal:bio:")
    )

    assert (
        len(
            observations,
        )
        == 2
    )

    assert {observation.correlation_key for observation in observations} == {
        f"profile-purpose:{snapshot.id}:bio"
    }


def test_display_name_and_bio_are_independent_correlation_sources() -> None:
    snapshot = build_snapshot(
        display_name="Content Creator",
        bio="Content Creator",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    observations = tuple(
        observation
        for observation in result.observations
        if observation.source.startswith("profile_purpose_signal:")
    )

    assert (
        len(
            observations,
        )
        == 2
    )

    assert {observation.correlation_key for observation in observations} == {
        (f"profile-purpose:{snapshot.id}:display-name"),
        (f"profile-purpose:{snapshot.id}:bio"),
    }


def test_purpose_analysis_does_not_create_new_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | Content Creator",
        ),
        reference_date=REFERENCE_DATE,
    )

    fact_kinds = {fact.kind for fact in result.facts}

    assert len(fact_kinds) == 4
