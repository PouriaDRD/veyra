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
