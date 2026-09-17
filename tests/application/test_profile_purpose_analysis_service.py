"""End-to-end tests for profile-purpose analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import FactKind
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisResult,
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


def purpose_for(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> HypothesisResult:
    """Analyze one fixture and return its profile-purpose hypothesis."""

    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio=bio,
            display_name=display_name,
        ),
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.PROFILE_PURPOSE,
    )

    assert hypothesis is not None

    return hypothesis


def test_professional_bio_produces_professional_hypothesis() -> None:
    hypothesis = purpose_for(
        bio="Software Engineer | Python",
    )

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value

    assert hypothesis.status is HypothesisStatus.PROBABLE


def test_persian_professional_bio_is_supported() -> None:
    hypothesis = purpose_for(
        bio="مهندس نرم افزار | پایتون",
    )

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value

    assert hypothesis.status is HypothesisStatus.PROBABLE


def test_creator_bio_produces_creator_hypothesis() -> None:
    hypothesis = purpose_for(
        bio="Content Creator | YouTuber",
    )

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_creator_bio_is_supported() -> None:
    hypothesis = purpose_for(
        bio="تولید محتوا | بلاگر",
    )

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_business_bio_produces_business_hypothesis() -> None:
    hypothesis = purpose_for(
        bio="Online Shop | DM for order",
    )

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_business_bio_is_supported() -> None:
    hypothesis = purpose_for(
        bio="فروشگاه | ثبت سفارش",
    )

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_organization_bio_produces_organization_hypothesis() -> None:
    hypothesis = purpose_for(
        bio="Nonprofit Foundation",
    )

    assert hypothesis.best_value == ProfilePurpose.ORGANIZATION.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_personal_profile_marker_is_supported() -> None:
    hypothesis = purpose_for(
        bio="Personal account | my life",
    )

    assert hypothesis.best_value == ProfilePurpose.PERSONAL.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_display_name_can_supply_profile_purpose_signal() -> None:
    hypothesis = purpose_for(
        display_name="Content Creator",
        bio="Coffee | Tehran",
    )

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_unrelated_profile_text_returns_unknown_purpose() -> None:
    hypothesis = purpose_for(
        display_name="Sara",
        bio="Coffee | Tehran | Music",
    )

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_business_signal_outweighs_professional_signal() -> None:
    hypothesis = purpose_for(
        bio="Software Engineer | Online Shop",
    )

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value


def test_creator_and_business_same_bio_remain_ambiguous() -> None:
    hypothesis = purpose_for(
        bio="Content Creator | Online Shop",
    )

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

    assert len(observations) == 2

    assert {observation.correlation_key for observation in observations} == {
        f"profile-purpose:{snapshot.id}:bio",
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

    assert len(observations) == 2

    assert {observation.correlation_key for observation in observations} == {
        f"profile-purpose:{snapshot.id}:display-name",
        f"profile-purpose:{snapshot.id}:bio",
    }


def test_purpose_analysis_does_not_create_profile_purpose_fact() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | Content Creator",
        ),
        reference_date=REFERENCE_DATE,
    )

    fact_kinds = {fact.kind for fact in result.facts}

    assert fact_kinds == {
        FactKind.BIRTH_YEAR,
        FactKind.RELATIONSHIP_STATUS,
        FactKind.CITY,
        FactKind.COUNTRY,
        FactKind.OCCUPATION,
        FactKind.EMPLOYER,
    }


# ============================================================
# BUSINESS FALSE-POSITIVE REGRESSIONS
# ============================================================


def test_business_student_does_not_become_business_profile() -> None:
    hypothesis = purpose_for(
        bio="Business student",
    )

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_business_analyst_remains_professional() -> None:
    hypothesis = purpose_for(
        bio="Business Analyst",
    )

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value

    assert hypothesis.status is HypothesisStatus.PROBABLE


def test_brand_designer_remains_professional() -> None:
    hypothesis = purpose_for(
        bio="Brand Designer",
    )

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value


def test_company_employment_mention_does_not_make_profile_business() -> None:
    hypothesis = purpose_for(
        bio="Software Engineer at Acme Company",
    )

    assert hypothesis.best_value == ProfilePurpose.PROFESSIONAL.value


def test_company_display_name_can_identify_business_profile() -> None:
    hypothesis = purpose_for(
        display_name="Acme Company",
    )

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_company_display_name_can_identify_business_profile() -> None:
    hypothesis = purpose_for(
        display_name="شرکت ویرا",
    )

    assert hypothesis.best_value == ProfilePurpose.BUSINESS.value


# ============================================================
# ORGANIZATION FALSE-POSITIVE REGRESSIONS
# ============================================================


def test_university_student_bio_does_not_make_profile_organization() -> None:
    hypothesis = purpose_for(
        bio="Student at Tehran University",
    )

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_university_display_name_can_identify_organization() -> None:
    hypothesis = purpose_for(
        display_name="Tehran University",
    )

    assert hypothesis.best_value == ProfilePurpose.ORGANIZATION.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_official_university_bio_can_identify_organization() -> None:
    hypothesis = purpose_for(
        bio="Official account of Tehran University",
    )

    assert hypothesis.best_value == ProfilePurpose.ORGANIZATION.value


def test_persian_university_student_bio_does_not_make_organization() -> None:
    hypothesis = purpose_for(
        bio="دانشجوی دانشگاه تهران",
    )

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == ProfilePurpose.UNKNOWN.value


def test_persian_official_university_bio_can_identify_organization() -> None:
    hypothesis = purpose_for(
        bio="صفحه رسمی دانشگاه تهران",
    )

    assert hypothesis.best_value == ProfilePurpose.ORGANIZATION.value


# ============================================================
# SOURCE-AWARE INTEGRATION
# ============================================================


def test_same_institution_text_has_different_semantics_by_field() -> None:
    bio_hypothesis = purpose_for(
        bio="Tehran University",
    )

    display_name_hypothesis = purpose_for(
        display_name="Tehran University",
    )

    assert bio_hypothesis.status is HypothesisStatus.UNKNOWN

    assert display_name_hypothesis.best_value == ProfilePurpose.ORGANIZATION.value


def test_same_company_text_has_different_semantics_by_field() -> None:
    bio_hypothesis = purpose_for(
        bio="Acme Company",
    )

    display_name_hypothesis = purpose_for(
        display_name="Acme Company",
    )

    assert bio_hypothesis.status is HypothesisStatus.UNKNOWN

    assert display_name_hypothesis.best_value == ProfilePurpose.BUSINESS.value


# ============================================================
# MIXED PURPOSE SEMANTICS
# ============================================================


def test_independent_creator_display_name_and_business_bio_become_mixed() -> None:
    hypothesis = purpose_for(
        display_name="Content Creator",
        bio="Online Shop | DM for order",
    )

    assert hypothesis.best_value == ProfilePurpose.MIXED.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_independent_professional_display_name_and_creator_bio_become_mixed() -> None:
    hypothesis = purpose_for(
        display_name="Software Engineer",
        bio="Content Creator",
    )

    assert hypothesis.best_value == ProfilePurpose.MIXED.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_independent_business_display_name_and_organization_bio_become_mixed() -> None:
    hypothesis = purpose_for(
        display_name="Acme Company",
        bio="Nonprofit Foundation",
    )

    assert hypothesis.best_value == ProfilePurpose.MIXED.value


def test_same_bio_professional_and_creator_do_not_become_mixed() -> None:
    hypothesis = purpose_for(
        bio="Software Engineer | Content Creator",
    )

    assert hypothesis.best_value != ProfilePurpose.MIXED.value


def test_same_bio_creator_and_business_do_not_become_mixed() -> None:
    hypothesis = purpose_for(
        bio="Content Creator | Online Shop",
    )

    assert hypothesis.best_value != ProfilePurpose.MIXED.value


def test_same_purpose_across_display_name_and_bio_is_not_mixed() -> None:
    hypothesis = purpose_for(
        display_name="Content Creator",
        bio="Content Creator",
    )

    assert hypothesis.best_value == ProfilePurpose.CREATOR.value

    assert hypothesis.best_value != ProfilePurpose.MIXED.value


def test_personal_and_professional_sources_do_not_become_mixed() -> None:
    hypothesis = purpose_for(
        display_name="Personal Profile",
        bio="Software Engineer",
    )

    assert hypothesis.best_value != ProfilePurpose.MIXED.value


def test_mixed_hypothesis_retains_two_independent_supporting_observations() -> None:
    hypothesis = purpose_for(
        display_name="Content Creator",
        bio="Online Shop",
    )

    mixed = hypothesis.candidate_for(
        ProfilePurpose.MIXED.value,
    )

    assert mixed is not None

    assert (
        len(
            mixed.supporting_observations,
        )
        == 2
    )

    assert {observation.correlation_key for observation in mixed.supporting_observations}

    assert len({observation.correlation_key for observation in mixed.supporting_observations}) == 2


def test_mixed_explanations_retain_original_component_semantics() -> None:
    hypothesis = purpose_for(
        display_name="Content Creator",
        bio="Online Shop",
    )

    mixed = hypothesis.candidate_for(
        ProfilePurpose.MIXED.value,
    )

    assert mixed is not None

    explanations = {observation.explanation for observation in mixed.supporting_observations}

    assert any("'creator'" in explanation for explanation in explanations)

    assert any("'business'" in explanation for explanation in explanations)
