"""End-to-end tests for employer fact analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import (
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
    """Create one employer-analysis fixture."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="employer_test_1997",
        display_name=display_name,
        bio=bio,
    )


def employer_fact_for(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> Fact:
    """Analyze one snapshot and return its employer fact."""

    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio=bio,
            display_name=display_name,
        ),
        reference_date=REFERENCE_DATE,
    )

    return next(fact for fact in result.facts if fact.kind is FactKind.EMPLOYER)


def test_english_employer_is_supported() -> None:
    fact = employer_fact_for(
        bio="Software Engineer at Acme",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "acme"
    assert fact.confidence == 0.96


def test_works_at_employer_is_supported() -> None:
    fact = employer_fact_for(
        bio="Works at Acme",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "acme"


def test_persian_employer_is_supported() -> None:
    fact = employer_fact_for(
        bio="مهندس نرم افزار در دیجی کالا",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "دیجی کالا"


def test_persian_work_phrase_is_supported() -> None:
    fact = employer_fact_for(
        bio="در دیجی کالا کار می کنم",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "دیجی کالا"


def test_unknown_employer_creates_unknown_fact() -> None:
    fact = employer_fact_for(
        bio="Software Engineer | Tehran",
    )

    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None
    assert fact.confidence == 0
    assert fact.evidence == ()


def test_historical_employer_is_unknown() -> None:
    fact = employer_fact_for(
        bio="Former Software Engineer at Acme",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_recruiting_text_does_not_create_employer_fact() -> None:
    fact = employer_fact_for(
        bio="Hiring Software Engineer at Acme",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_educational_institution_does_not_create_employer_fact() -> None:
    fact = employer_fact_for(
        bio="Software Engineer at Tehran University",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_location_is_not_employer() -> None:
    fact = employer_fact_for(
        bio="Software Engineer in Tehran",
    )

    assert fact.status is FactStatus.UNKNOWN


def test_two_different_explicit_employers_create_conflicted_fact() -> None:
    fact = employer_fact_for(
        bio=("Works at Acme | Software Engineer at Veyra"),
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None

    assert {item.normalized_value for item in fact.evidence} == {
        "acme",
        "veyra",
    }


def test_duplicate_same_employer_does_not_conflict() -> None:
    fact = employer_fact_for(
        bio=("Works at Acme | Software Engineer at Acme"),
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "acme"

    assert len(fact.evidence) == 1


def test_occupation_and_employer_are_separate_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer at Acme",
        ),
        reference_date=REFERENCE_DATE,
    )

    occupation = next(fact for fact in result.facts if fact.kind is FactKind.OCCUPATION)

    employer = next(fact for fact in result.facts if fact.kind is FactKind.EMPLOYER)

    assert occupation.status is FactStatus.SUPPORTED
    assert occupation.value == "software engineer"

    assert employer.status is FactStatus.SUPPORTED
    assert employer.value == "acme"


def test_employer_evidence_is_in_flat_analysis_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Works at Acme",
        ),
        reference_date=REFERENCE_DATE,
    )

    evidence = tuple(item for item in result.evidence if item.extractor == "bio_employer_explicit")

    assert len(evidence) == 1
    assert evidence[0].normalized_value == "acme"


def test_employer_fact_coexists_with_other_fact_categories() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio=("متاهل | ساکن تهران | مهندس نرم افزار در دیجی کالا"),
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
