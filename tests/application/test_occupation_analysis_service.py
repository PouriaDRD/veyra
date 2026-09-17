"""End-to-end tests for occupation fact analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import (
    EvidenceSource,
    Fact,
    FactKind,
    FactStatus,
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
    """Create one profile-analysis fixture."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="occupation_test_1997",
        display_name=display_name,
        bio=bio,
    )


def occupation_fact_for(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> Fact:
    """Analyze one snapshot and return its occupation fact."""

    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio=bio,
            display_name=display_name,
        ),
        reference_date=REFERENCE_DATE,
    )

    fact = next(fact for fact in result.facts if fact.kind is FactKind.OCCUPATION)

    return fact


def test_occupation_fact_is_supported_from_english_bio() -> None:
    fact = occupation_fact_for(
        bio="Software Engineer",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "software engineer"
    assert fact.confidence == 0.96


def test_occupation_fact_is_supported_from_persian_bio() -> None:
    fact = occupation_fact_for(
        bio="مهندس نرم افزار",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "software engineer"


def test_display_name_can_support_occupation_fact() -> None:
    fact = occupation_fact_for(
        display_name="Product Designer",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "product designer"
    assert fact.confidence == 0.92


def test_same_occupation_from_two_sources_combines_support() -> None:
    fact = occupation_fact_for(
        display_name="Software Engineer",
        bio="Software Engineer | Python",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "software engineer"

    assert len(fact.evidence) == 2

    assert {item.source for item in fact.evidence} == {
        EvidenceSource.DISPLAY_NAME,
        EvidenceSource.BIO,
    }

    assert fact.confidence > 0.96


def test_conflicting_explicit_occupations_create_conflicted_fact() -> None:
    fact = occupation_fact_for(
        display_name="Software Engineer",
        bio="Photographer",
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None
    assert len(fact.evidence) == 2


def test_unknown_occupation_creates_unknown_fact() -> None:
    fact = occupation_fact_for(
        bio="Coffee | Tehran | Music",
    )

    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None
    assert fact.confidence == 0
    assert fact.evidence == ()


def test_historical_role_does_not_create_occupation_fact() -> None:
    fact = occupation_fact_for(
        bio="Former Software Engineer",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_recruiting_role_does_not_create_occupation_fact() -> None:
    fact = occupation_fact_for(
        bio="Hiring Software Engineer",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_negated_role_does_not_create_occupation_fact() -> None:
    fact = occupation_fact_for(
        bio="Not a Software Engineer",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_student_role_does_not_create_occupation_fact() -> None:
    fact = occupation_fact_for(
        bio="Student Software Engineer",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_specific_role_does_not_conflict_with_generic_nested_role() -> None:
    fact = occupation_fact_for(
        bio="Product Designer",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "product designer"
    assert len(fact.evidence) == 1


def test_occupation_fact_coexists_with_other_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="متاهل | ساکن تهران | مهندس نرم افزار",
        ),
        reference_date=REFERENCE_DATE,
    )

    fact_kinds = {fact.kind for fact in result.facts}

    assert fact_kinds == {
        FactKind.BIRTH_YEAR,
        FactKind.DECLARED_GENDER,
        FactKind.RELATIONSHIP_STATUS,
        FactKind.CITY,
        FactKind.COUNTRY,
        FactKind.OCCUPATION,
        FactKind.EMPLOYER,
        FactKind.INSTITUTION,
        FactKind.EDUCATION,
    }


def test_occupation_evidence_is_in_flat_analysis_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer",
        ),
        reference_date=REFERENCE_DATE,
    )

    occupation_evidence = tuple(
        item
        for item in result.evidence
        if item.extractor
        in {
            "bio_occupation_explicit",
            "display_name_occupation_explicit",
        }
    )

    assert len(occupation_evidence) == 1
    assert occupation_evidence[0].normalized_value == "software engineer"


def test_occupation_fact_does_not_replace_profile_purpose_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer",
        ),
        reference_date=REFERENCE_DATE,
    )

    occupation = next(fact for fact in result.facts if fact.kind is FactKind.OCCUPATION)

    purpose = next(
        hypothesis for hypothesis in result.hypotheses if hypothesis.kind.value == "profile_purpose"
    )

    assert occupation.status is FactStatus.SUPPORTED
    assert occupation.value == "software engineer"

    assert purpose.best_value == "professional"
