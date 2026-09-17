"""Tests for profile evidence analysis."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import (
    BirthYear,
    CalendarSystem,
    FactKind,
    FactStatus,
)
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisStatus,
    RelationshipStatus,
)
from veyra.domain.snapshots import ProfileSnapshot
from veyra.domain.validation import ValidationCode

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def build_snapshot(
    *,
    username: str,
    bio: str | None = None,
) -> ProfileSnapshot:
    """Create a profile snapshot for analysis tests."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username=username,
        bio=bio,
    )


def test_analysis_accepts_explicit_adult_birth_year() -> None:
    snapshot = build_snapshot(
        username="neda1997",
        bio="Designer from Tehran",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.SUPPORTED

    assert birth_year.value == BirthYear(
        year=1997,
        calendar=CalendarSystem.GREGORIAN,
    )

    assert result.validation.is_accepted is True
    assert result.validation.rejection_codes == ()

    assert result.snapshot_id == snapshot.id
    assert result.profile_id == snapshot.profile_id


def test_analysis_rejects_profile_without_age_evidence() -> None:
    snapshot = build_snapshot(
        username="veyra_user",
        bio="Designer from Tehran",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.UNKNOWN
    assert birth_year.value is None

    assert result.validation.is_accepted is False

    assert result.validation.rejection_codes == (ValidationCode.AGE_UNCERTAIN,)


def test_analysis_preserves_ambiguous_username() -> None:
    snapshot = build_snapshot(
        username="hasti88",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.CONFLICTED
    assert birth_year.value is None

    assert len(result.evidence) == 2
    assert all(evidence.is_ambiguous for evidence in result.evidence)

    assert result.validation.is_accepted is False

    assert result.validation.rejection_codes == (
        ValidationCode.CONFLICTING_EVIDENCE,
        ValidationCode.AGE_UNCERTAIN,
    )


def test_explicit_bio_resolves_ambiguous_username() -> None:
    snapshot = build_snapshot(
        username="hasti88",
        bio=("\u0645\u062a\u0648\u0644\u062f \u06f1\u06f3\u06f8\u06f8"),
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.SUPPORTED

    assert birth_year.value == BirthYear(
        year=1388,
        calendar=CalendarSystem.SOLAR_HIJRI,
    )

    # 1388 Solar Hijri corresponds to a minor/possibly underage person
    # at the 2026 reference date, therefore analysis must not accept it.
    assert result.validation.is_accepted is False

    assert ValidationCode.POSSIBLE_MINOR in result.validation.rejection_codes


def test_analysis_detects_definitive_birth_year_conflict() -> None:
    snapshot = build_snapshot(
        username="neda1999",
        bio="born 2001",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.CONFLICTED
    assert birth_year.value is None

    assert result.validation.is_accepted is False

    assert result.validation.rejection_codes == (
        ValidationCode.CONFLICTING_EVIDENCE,
        ValidationCode.AGE_UNCERTAIN,
    )


def test_analysis_combines_matching_username_and_bio_evidence() -> None:
    snapshot = build_snapshot(
        username="neda1997",
        bio="born 1997",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    birth_year = result.fact_for(
        FactKind.BIRTH_YEAR,
    )

    assert birth_year is not None
    assert birth_year.status is FactStatus.SUPPORTED

    assert birth_year.value == BirthYear(
        year=1997,
        calendar=CalendarSystem.GREGORIAN,
    )

    assert birth_year.confidence == 0.9875
    assert len(birth_year.evidence) == 2

    assert result.validation.is_accepted is True


def test_analysis_extracts_english_relationship_fact() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="Designer | Married 💍 | Tehran",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None

    assert relationship.status is FactStatus.SUPPORTED

    assert relationship.value == RelationshipStatus.MARRIED.value

    assert relationship.confidence == 0.98


def test_analysis_extracts_persian_relationship_fact() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="طراح گرافیک | تهران | مجرد",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None

    assert relationship.status is FactStatus.SUPPORTED

    assert relationship.value == RelationshipStatus.SINGLE.value


def test_analysis_builds_relationship_hypothesis_from_explicit_fact() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="متاهل",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert hypothesis is not None

    assert hypothesis.best_value == RelationshipStatus.MARRIED.value

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_analysis_builds_contextual_relationship_observations() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="Sara 💍 ❤️",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None

    assert relationship.status is FactStatus.UNKNOWN

    assert result.observations

    targets = {observation.target_value for observation in result.observations}

    assert RelationshipStatus.MARRIED.value in targets

    assert RelationshipStatus.ENGAGED.value in targets

    assert RelationshipStatus.IN_RELATIONSHIP.value in targets

    assert RelationshipStatus.SINGLE.value not in targets


def test_analysis_does_not_convert_emoji_signal_into_explicit_fact() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="علی ❤️",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None

    assert relationship.status is FactStatus.UNKNOWN

    assert relationship.value is None


def test_analysis_preserves_explicit_single_over_contextual_signal() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="مجرد | Ali ❤️",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None
    assert hypothesis is not None

    assert relationship.value == RelationshipStatus.SINGLE.value

    assert hypothesis.best_value == RelationshipStatus.SINGLE.value


def test_analysis_supports_mixed_persian_english_relationship_data() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="Graphic Designer | تهران | متاهل 💍",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None
    assert hypothesis is not None

    assert relationship.value == RelationshipStatus.MARRIED.value

    assert hypothesis.best_value == RelationshipStatus.MARRIED.value


def test_analysis_preserves_conflicting_relationship_claims() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="Single | متاهل",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None
    assert hypothesis is not None

    assert relationship.status is FactStatus.CONFLICTED

    assert hypothesis.status is HypothesisStatus.CONFLICTED


def test_analysis_returns_unknown_relationship_without_evidence() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="Designer from Tehran",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    relationship = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert relationship is not None
    assert hypothesis is not None

    assert relationship.status is FactStatus.UNKNOWN

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == RelationshipStatus.UNKNOWN.value


def test_persian_only_contextual_relationship_signal_remains_ambiguous() -> None:
    snapshot = build_snapshot(
        username="sara1997",
        bio="علی 💍 ❤️",
    )

    result = ProfileAnalysisService().analyze(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    fact = result.fact_for(
        FactKind.RELATIONSHIP_STATUS,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    assert fact is not None
    assert hypothesis is not None

    assert fact.status is FactStatus.UNKNOWN

    assert hypothesis.status is HypothesisStatus.AMBIGUOUS

    assert hypothesis.best_value == RelationshipStatus.UNKNOWN.value
