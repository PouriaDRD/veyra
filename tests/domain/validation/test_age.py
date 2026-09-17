"""Tests for adult age validation."""

from datetime import date

from veyra.domain.evidence import (
    BirthYear,
    CalendarSystem,
    Evidence,
    EvidenceSource,
    Fact,
    FactKind,
    FactStatus,
)
from veyra.domain.validation import (
    AdultAgeValidator,
    ValidationCode,
)

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def build_supported_birth_year(
    year: int,
    *,
    confidence: float = 0.9,
    calendar: CalendarSystem = CalendarSystem.GREGORIAN,
) -> Fact:
    """Create supported birth-year fact."""

    birth_year = BirthYear(
        year=year,
        calendar=calendar,
    )

    evidence = Evidence(
        source=EvidenceSource.BIO,
        raw_value=str(year),
        normalized_value=birth_year,
        confidence=confidence,
    )

    return Fact(
        kind=FactKind.BIRTH_YEAR,
        status=FactStatus.SUPPORTED,
        value=birth_year,
        confidence=confidence,
        evidence=(evidence,),
    )


def build_supported_age(
    age: int,
    *,
    confidence: float = 0.9,
) -> Fact:
    """Create supported exact-age fact."""

    evidence = Evidence(
        source=EvidenceSource.BIO,
        raw_value=str(age),
        normalized_value=age,
        confidence=confidence,
    )

    return Fact(
        kind=FactKind.AGE,
        status=FactStatus.SUPPORTED,
        value=age,
        confidence=confidence,
        evidence=(evidence,),
    )


def test_validator_accepts_confident_adult_birth_year() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            2000,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is True
    assert result.rejection_codes == ()


def test_validator_accepts_exact_age_at_adult_boundary() -> None:
    result = AdultAgeValidator().validate(
        build_supported_age(
            18,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is True


def test_validator_rejects_minor() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            2010,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.POSSIBLE_MINOR,)


def test_validator_rejects_exact_minor_age() -> None:
    result = AdultAgeValidator().validate(
        build_supported_age(
            17,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.POSSIBLE_MINOR,)


def test_validator_treats_boundary_birth_year_as_uncertain() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            2008,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.AGE_UNCERTAIN,)


def test_validator_rejects_low_confidence_age() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            2000,
            confidence=0.4,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.AGE_UNCERTAIN,)


def test_validator_rejects_unknown_age() -> None:
    fact = Fact(
        kind=FactKind.BIRTH_YEAR,
        status=FactStatus.UNKNOWN,
        confidence=0,
    )

    result = AdultAgeValidator().validate(
        fact,
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.AGE_UNCERTAIN,)


def test_validator_rejects_conflicting_age_evidence() -> None:
    fact = Fact(
        kind=FactKind.BIRTH_YEAR,
        status=FactStatus.CONFLICTED,
        confidence=0.8,
        evidence=(
            Evidence(
                source=EvidenceSource.USERNAME,
                raw_value="1999",
                normalized_value=1999,
                confidence=0.8,
            ),
            Evidence(
                source=EvidenceSource.BIO,
                raw_value="2001",
                normalized_value=2001,
                confidence=0.95,
            ),
        ),
    )

    result = AdultAgeValidator().validate(
        fact,
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (
        ValidationCode.CONFLICTING_EVIDENCE,
        ValidationCode.AGE_UNCERTAIN,
    )


def test_validator_handles_confident_solar_hijri_adult() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            1380,
            calendar=CalendarSystem.SOLAR_HIJRI,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is True


def test_validator_rejects_solar_hijri_minor() -> None:
    result = AdultAgeValidator().validate(
        build_supported_birth_year(
            1395,
            calendar=CalendarSystem.SOLAR_HIJRI,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.POSSIBLE_MINOR,)
