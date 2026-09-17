"""Tests for birth-year evidence extractors."""

from veyra.domain.evidence import (
    BioBirthYearExtractor,
    BirthYear,
    CalendarSystem,
    FactKind,
    FactResolver,
    FactStatus,
    UsernameBirthYearExtractor,
    normalize_digits,
)


def test_normalize_digits_supports_persian_digits() -> None:
    assert (
        normalize_digits(
            "\u06f1\u06f3\u06f8\u06f8",
        )
        == "1388"
    )


def test_username_extracts_gregorian_birth_year() -> None:
    evidence = UsernameBirthYearExtractor().extract(
        "neda1997",
    )

    assert len(evidence) == 1

    assert evidence[0].normalized_value == BirthYear(
        year=1997,
        calendar=CalendarSystem.GREGORIAN,
    )


def test_username_extracts_solar_hijri_birth_year() -> None:
    evidence = UsernameBirthYearExtractor().extract(
        "hasti1388",
    )

    assert len(evidence) == 1

    assert evidence[0].normalized_value == BirthYear(
        year=1388,
        calendar=CalendarSystem.SOLAR_HIJRI,
    )


def test_username_supports_persian_digits() -> None:
    evidence = UsernameBirthYearExtractor().extract(
        "hasti\u06f1\u06f3\u06f8\u06f8",
    )

    assert len(evidence) == 1

    assert evidence[0].normalized_value == BirthYear(
        year=1388,
        calendar=CalendarSystem.SOLAR_HIJRI,
    )


def test_two_digit_username_remains_ambiguous() -> None:
    evidence = UsernameBirthYearExtractor().extract(
        "hasti88",
    )

    assert len(evidence) == 2

    fact = FactResolver().resolve(
        FactKind.BIRTH_YEAR,
        evidence,
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None


def test_x99_remains_ambiguous() -> None:
    evidence = UsernameBirthYearExtractor().extract(
        "x99",
    )

    values = {item.normalized_value for item in evidence}

    assert values == {
        BirthYear(
            year=1999,
            calendar=CalendarSystem.GREGORIAN,
        ),
        BirthYear(
            year=1399,
            calendar=CalendarSystem.SOLAR_HIJRI,
        ),
    }


def test_bio_extracts_explicit_gregorian_year() -> None:
    evidence = BioBirthYearExtractor().extract(
        "Designer | born 1997 | Tehran",
    )

    assert len(evidence) == 1
    assert evidence[0].confidence == 0.95

    assert evidence[0].normalized_value == BirthYear(
        year=1997,
        calendar=CalendarSystem.GREGORIAN,
    )


def test_bio_extracts_explicit_solar_hijri_year() -> None:
    evidence = BioBirthYearExtractor().extract(
        "طراح | متولد ۱۳۸۸ | تهران",
    )

    assert len(evidence) == 1
    assert evidence[0].confidence == 0.95

    assert evidence[0].normalized_value == BirthYear(
        year=1388,
        calendar=CalendarSystem.SOLAR_HIJRI,
    )


def test_bio_extracts_isolated_year_with_lower_confidence() -> None:
    evidence = BioBirthYearExtractor().extract(
        "Tehran • 1997 • Designer",
    )

    assert len(evidence) == 1
    assert evidence[0].confidence == 0.6


def test_extractors_ignore_text_without_year() -> None:
    assert (
        UsernameBirthYearExtractor().extract(
            "veyra_user",
        )
        == ()
    )

    assert (
        BioBirthYearExtractor().extract(
            "Designer from Tehran",
        )
        == ()
    )
