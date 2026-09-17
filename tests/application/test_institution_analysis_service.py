"""End-to-end tests for institution fact analysis."""

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
    """Create one institution-analysis fixture."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="institution_test_1997",
        display_name=display_name,
        bio=bio,
    )


def institution_fact_for(
    *,
    bio: str | None = None,
    display_name: str | None = None,
) -> Fact:
    """Analyze one snapshot and return its institution fact."""

    result = ProfileAnalysisService().analyze(
        build_snapshot(bio=bio, display_name=display_name),
        reference_date=REFERENCE_DATE,
    )
    return next(fact for fact in result.facts if fact.kind is FactKind.INSTITUTION)


def test_english_student_institution_is_supported() -> None:
    fact = institution_fact_for(bio="Student at Tehran University")
    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "tehran university"
    assert fact.confidence == 0.97


def test_persian_student_institution_is_supported() -> None:
    fact = institution_fact_for(bio="دانشجوی دانشگاه تهران")
    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "دانشگاه تهران"


def test_historical_graduate_institution_is_supported() -> None:
    fact = institution_fact_for(bio="Graduate of Sharif University")
    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "sharif university"


def test_unknown_institution_creates_unknown_fact() -> None:
    fact = institution_fact_for(bio="Software Engineer | Tehran")
    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None
    assert fact.confidence == 0
    assert fact.evidence == ()


def test_plain_institution_mention_remains_unknown() -> None:
    assert institution_fact_for(bio="Tehran University").status is FactStatus.UNKNOWN


def test_employment_at_university_does_not_create_institution_fact() -> None:
    fact = institution_fact_for(bio="Software Engineer at Tehran University")
    assert fact.status is FactStatus.UNKNOWN


def test_two_different_explicit_institutions_create_conflict() -> None:
    fact = institution_fact_for(
        bio="Graduate of Sharif University | Student at MIT",
    )
    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None
    assert {item.normalized_value for item in fact.evidence} == {
        "sharif university",
        "mit",
    }


def test_duplicate_same_institution_does_not_conflict() -> None:
    fact = institution_fact_for(bio="Graduate of MIT | Student at MIT")
    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == "mit"
    assert len(fact.evidence) == 1


def test_institution_evidence_is_in_flat_analysis_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(bio="Student at Tehran University"),
        reference_date=REFERENCE_DATE,
    )
    evidence = tuple(
        item for item in result.evidence if item.extractor == "bio_institution_explicit"
    )
    assert len(evidence) == 1
    assert evidence[0].normalized_value == "tehran university"


def test_institution_and_occupation_are_separate_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(bio="Software Engineer | Student at Tehran University"),
        reference_date=REFERENCE_DATE,
    )
    occupation = next(fact for fact in result.facts if fact.kind is FactKind.OCCUPATION)
    institution = next(fact for fact in result.facts if fact.kind is FactKind.INSTITUTION)
    assert occupation.status is FactStatus.SUPPORTED
    assert occupation.value == "software engineer"
    assert institution.status is FactStatus.SUPPORTED
    assert institution.value == "tehran university"


def test_institution_and_employer_are_separate_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(bio="Software Engineer at Acme | Student at MIT"),
        reference_date=REFERENCE_DATE,
    )
    employer = next(fact for fact in result.facts if fact.kind is FactKind.EMPLOYER)
    institution = next(fact for fact in result.facts if fact.kind is FactKind.INSTITUTION)
    assert employer.status is FactStatus.SUPPORTED
    assert employer.value == "acme"
    assert institution.status is FactStatus.SUPPORTED
    assert institution.value == "mit"


def test_result_contains_institution_fact_even_when_unknown() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(bio="Coffee | Music"),
        reference_date=REFERENCE_DATE,
    )
    fact = next(fact for fact in result.facts if fact.kind is FactKind.INSTITUTION)
    assert fact.status is FactStatus.UNKNOWN


def test_institution_fact_does_not_create_new_hypothesis_kind() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(bio="Student at Tehran University"),
        reference_date=REFERENCE_DATE,
    )
    assert len(result.hypotheses) == 3
