"""Explicit birth-year evidence extractors."""

import re
from dataclasses import dataclass

from ..birth_year import BirthYear, CalendarSystem
from ..entities import Evidence
from ..enums import EvidenceSource

_DIGIT_TRANSLATION = str.maketrans(
    {
        "\u06f0": "0",
        "\u06f1": "1",
        "\u06f2": "2",
        "\u06f3": "3",
        "\u06f4": "4",
        "\u06f5": "5",
        "\u06f6": "6",
        "\u06f7": "7",
        "\u06f8": "8",
        "\u06f9": "9",
        "\u0660": "0",
        "\u0661": "1",
        "\u0662": "2",
        "\u0663": "3",
        "\u0664": "4",
        "\u0665": "5",
        "\u0666": "6",
        "\u0667": "7",
        "\u0668": "8",
        "\u0669": "9",
    }
)

_FOUR_DIGIT_YEAR_PATTERN = re.compile(r"(?<!\d)(?P<year>(?:13|14|19|20)\d{2})(?!\d)")

_TWO_DIGIT_YEAR_PATTERN = re.compile(r"(?<!\d)(?P<year>\d{2})(?!\d)")

_BIO_EXPLICIT_YEAR_PATTERN = re.compile(
    r"""
    (?:
        born(?:\s+in)?
        |
        birth(?:\s+year)?
        |
        متولد
        |
        تولد
    )
    [\s:_\-]*
    (?P<year>(?:13|14|19|20)\d{2})
    """,
    re.IGNORECASE | re.VERBOSE,
)


def normalize_digits(
    value: str,
) -> str:
    """Normalize Persian and Arabic digits to ASCII."""

    return value.translate(
        _DIGIT_TRANSLATION,
    )


def _normalize_four_digit_year(
    year: int,
) -> BirthYear | None:
    """Normalize a recognizable four-digit calendar year."""

    if 1900 <= year <= 2099:
        return BirthYear(
            year=year,
            calendar=CalendarSystem.GREGORIAN,
        )

    if 1300 <= year <= 1499:
        return BirthYear(
            year=year,
            calendar=CalendarSystem.SOLAR_HIJRI,
        )

    return None


@dataclass(frozen=True, slots=True)
class UsernameBirthYearExtractor:
    """
    Extract explicit-looking birth years from usernames.

    Four-digit values are stronger evidence. Two-digit suffixes remain
    intentionally ambiguous and produce multiple low-confidence candidates.
    """

    four_digit_confidence: float = 0.75
    two_digit_confidence: float = 0.25

    def extract(
        self,
        username: str,
    ) -> tuple[Evidence, ...]:
        """Extract birth-year evidence from a username."""

        normalized_username = normalize_digits(
            username.strip().removeprefix("@"),
        )

        four_digit_matches = tuple(
            _FOUR_DIGIT_YEAR_PATTERN.finditer(
                normalized_username,
            )
        )

        evidence: list[Evidence] = []

        for match in four_digit_matches:
            raw_year = match.group("year")
            birth_year = _normalize_four_digit_year(
                int(raw_year),
            )

            if birth_year is None:
                continue

            evidence.append(
                Evidence(
                    source=EvidenceSource.USERNAME,
                    raw_value=raw_year,
                    normalized_value=birth_year,
                    confidence=self.four_digit_confidence,
                    extractor="username_birth_year",
                )
            )

        if evidence:
            return tuple(evidence)

        two_digit_matches = tuple(
            _TWO_DIGIT_YEAR_PATTERN.finditer(
                normalized_username,
            )
        )

        for match in two_digit_matches:
            raw_year = match.group("year")
            short_year = int(raw_year)

            evidence.extend(
                (
                    Evidence(
                        source=EvidenceSource.USERNAME,
                        raw_value=raw_year,
                        normalized_value=BirthYear(
                            year=1900 + short_year,
                            calendar=CalendarSystem.GREGORIAN,
                        ),
                        confidence=self.two_digit_confidence,
                        extractor="username_birth_year_ambiguous",
                        is_ambiguous=True,
                    ),
                    Evidence(
                        source=EvidenceSource.USERNAME,
                        raw_value=raw_year,
                        normalized_value=BirthYear(
                            year=1300 + short_year,
                            calendar=CalendarSystem.SOLAR_HIJRI,
                        ),
                        confidence=self.two_digit_confidence,
                        extractor="username_birth_year_ambiguous",
                        is_ambiguous=True,
                    ),
                )
            )

        return tuple(evidence)


@dataclass(frozen=True, slots=True)
class BioBirthYearExtractor:
    """
    Extract explicit birth-year statements from profile biographies.

    Explicit language such as ``born 1997`` or ``متولد ۱۳۸۸`` receives
    stronger confidence than an isolated four-digit year.
    """

    explicit_confidence: float = 0.95
    isolated_confidence: float = 0.6

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract birth-year evidence from biography text."""

        normalized_bio = normalize_digits(
            bio.strip(),
        )

        explicit_matches = tuple(
            _BIO_EXPLICIT_YEAR_PATTERN.finditer(
                normalized_bio,
            )
        )

        evidence: list[Evidence] = []

        consumed_spans: set[tuple[int, int]] = set()

        for match in explicit_matches:
            raw_year = match.group("year")
            birth_year = _normalize_four_digit_year(
                int(raw_year),
            )

            if birth_year is None:
                continue

            evidence.append(
                Evidence(
                    source=EvidenceSource.BIO,
                    raw_value=raw_year,
                    normalized_value=birth_year,
                    confidence=self.explicit_confidence,
                    extractor="bio_birth_year_explicit",
                )
            )

            consumed_spans.add(
                match.span("year"),
            )

        for match in _FOUR_DIGIT_YEAR_PATTERN.finditer(
            normalized_bio,
        ):
            if match.span("year") in consumed_spans:
                continue

            raw_year = match.group("year")
            birth_year = _normalize_four_digit_year(
                int(raw_year),
            )

            if birth_year is None:
                continue

            evidence.append(
                Evidence(
                    source=EvidenceSource.BIO,
                    raw_value=raw_year,
                    normalized_value=birth_year,
                    confidence=self.isolated_confidence,
                    extractor="bio_birth_year_isolated",
                )
            )

        return tuple(evidence)
