"""End-to-end tests for EDUCATION fact analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import Fact, FactKind, FactStatus
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(2026, 9, 17)


def build_snapshot(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> ProfileSnapshot:
    """Create one education-analysis fixture."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="education_test_1997",
        display_name=display_name,
        bio=bio,
    )


def education_fact_for(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> Fact:
    """Analyze one snapshot and return EDUCATION fact."""

    result = ProfileAnalysisService().analyze(
        build_snapshot(bio=bio, display_name=display_name),
        reference_date=REFERENCE_DATE,
    )

    return next(fact for fact in result.facts if fact.kind is FactKind.EDUCATION)


def test_english_education_fact_is_supported() -> None:
    fact = education_fact_for(
        bio="BSc Computer Science",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value is None
    assert fact.values == ("bachelor:computer science",)
    assert fact.confidence == 0.97


def test_persian_education_fact_is_supported() -> None:
    fact = education_fact_for(
        bio="کارشناسی ارشد علوم داده",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value is None
    assert fact.values == ("master:علوم داده",)


def test_unknown_education_creates_unknown_fact() -> None:
    fact = education_fact_for(
        bio="Student at MIT",
    )

    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None
    assert fact.values == ()
    assert fact.confidence == 0
    assert fact.evidence == ()


def test_field_without_degree_does_not_create_education_fact() -> None:
    fact = education_fact_for(
        bio="Computer Science",
    )

    assert fact.status is FactStatus.UNKNOWN
    assert fact.values == ()


def test_two_distinct_explicit_education_values_are_supported_together() -> None:
    fact = education_fact_for(
        bio="BSc Computer Science | MSc Data Science",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value is None
    assert fact.values == (
        "bachelor:computer science",
        "master:data science",
    )

    assert {item.normalized_value for item in fact.evidence} == {
        "bachelor:computer science",
        "master:data science",
    }


def test_duplicate_same_education_value_is_deduplicated() -> None:
    fact = education_fact_for(
        bio="BSc Computer Science | BSc Computer Science",
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value is None
    assert fact.values == ("bachelor:computer science",)
    assert len(fact.evidence) == 1


def test_education_evidence_is_in_flat_analysis_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="MSc Data Science",
        ),
        reference_date=REFERENCE_DATE,
    )

    evidence = tuple(item for item in result.evidence if item.extractor == "bio_education_explicit")

    assert len(evidence) == 1
    assert evidence[0].normalized_value == "master:data science"


def test_education_and_institution_are_separate_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="BSc Computer Science | Student at MIT",
        ),
        reference_date=REFERENCE_DATE,
    )

    education = next(fact for fact in result.facts if fact.kind is FactKind.EDUCATION)

    institution = next(fact for fact in result.facts if fact.kind is FactKind.INSTITUTION)

    assert education.status is FactStatus.SUPPORTED
    assert education.values == ("bachelor:computer science",)

    assert institution.status is FactStatus.SUPPORTED
    assert institution.values == ("mit",)


def test_education_and_occupation_are_separate_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | MSc Data Science",
        ),
        reference_date=REFERENCE_DATE,
    )

    occupation = next(fact for fact in result.facts if fact.kind is FactKind.OCCUPATION)

    education = next(fact for fact in result.facts if fact.kind is FactKind.EDUCATION)

    assert occupation.status is FactStatus.SUPPORTED
    assert occupation.value == "software engineer"

    assert education.status is FactStatus.SUPPORTED
    assert education.values == ("master:data science",)


def test_result_contains_education_fact_even_when_unknown() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Coffee | Tehran",
        ),
        reference_date=REFERENCE_DATE,
    )

    education = next(fact for fact in result.facts if fact.kind is FactKind.EDUCATION)

    assert education.status is FactStatus.UNKNOWN
    assert education.values == ()


def test_education_does_not_create_new_hypothesis_kind() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="BSc Computer Science",
        ),
        reference_date=REFERENCE_DATE,
    )

    assert len(result.hypotheses) == 3
