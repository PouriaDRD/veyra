"""Explicit education-institution evidence extraction."""

import re
from dataclasses import dataclass

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    normalize_text,
)

from ..entities import Evidence
from ..enums import EvidenceSource

# ============================================================
# CAPTURE BOUNDARIES
# ============================================================


_INSTITUTION_STOP_CHARS = r"\n|•;,،"
_INSTITUTION_VALUE = r"(?P<institution>[^\n|•;,،]{2,100}?)"


# ============================================================
# ENGLISH RELATION PATTERNS
# ============================================================


_ENGLISH_STUDENT_AT_PATTERN = re.compile(
    rf"\b(?:student|undergraduate|postgraduate|phd student|doctoral student)"
    rf"\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_STUDYING_AT_PATTERN = re.compile(
    rf"\b(?:studying|study)\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_GRADUATE_OF_PATTERN = re.compile(
    rf"\b(?:graduate|alumnus|alumna|alumni)\s+of\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_EDUCATED_AT_PATTERN = re.compile(
    rf"\beducated\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
    re.IGNORECASE,
)


# ============================================================
# PERSIAN RELATION PATTERNS
# ============================================================


_PERSIAN_STUDENT_OF_PATTERN = re.compile(
    rf"(?:دانشجو|دانشجوی)\s+(?:در\s+)?{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
)

_PERSIAN_STUDYING_AT_PATTERN = re.compile(
    rf"(?:در\s+حال\s+تحصیل|مشغول\s+به\s+تحصیل)\s+"
    rf"(?:در\s+)?{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
)

_PERSIAN_GRADUATE_OF_PATTERN = re.compile(
    rf"(?:فارغ\s+التحصیل|فارغ‌التحصیل)\s+(?:از\s+)?"
    rf"{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
)

_PERSIAN_EDUCATED_AT_PATTERN = re.compile(
    rf"(?:تحصیل\s+در|تحصیل\s+کرده\s+در)\s+"
    rf"{_INSTITUTION_VALUE}"
    rf"(?=$|[{_INSTITUTION_STOP_CHARS}])",
)


# ============================================================
# INSTITUTION VALUE NORMALIZATION
# ============================================================


_LEADING_INSTITUTION_ARTICLE = re.compile(
    r"^the\s+",
    re.IGNORECASE,
)

_TRAILING_RELATION_NOISE = re.compile(
    r"""
    \s+
    (?:
        student |
        graduate |
        alumnus |
        alumna |
        alumni
    )
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

_URL_PATTERN = re.compile(
    r"(?:https?://|www\.)",
    re.IGNORECASE,
)

_SOCIAL_HANDLE_PATTERN = re.compile(
    r"^@\w+$",
    re.UNICODE,
)

_OBVIOUS_NON_INSTITUTION_VALUES = frozenset(
    {
        "tehran",
        "iran",
        "london",
        "تهران",
        "ایران",
        "لندن",
        "home",
        "work",
        "خانه",
        "محل کار",
    }
)

_EMPLOYMENT_PREFIXES = (
    "works at",
    "work at",
    "working at",
    "employed at",
    "employee at",
    "software engineer at",
    "developer at",
    "engineer at",
    "designer at",
    "کار می کنم",
    "کار می‌کنم",
)


def _clean_institution_value(
    value: str,
) -> str:
    """Normalize one explicit institution name."""

    normalized = normalize_text(
        value,
    )

    normalized = normalized.strip(" .:-/")

    normalized = _LEADING_INSTITUTION_ARTICLE.sub(
        "",
        normalized,
    )

    normalized = _TRAILING_RELATION_NOISE.sub(
        "",
        normalized,
    )

    return normalized.strip(" .:-/")


def _is_valid_institution_value(
    value: str,
) -> bool:
    """Return whether one captured value can safely represent an institution."""

    if not value:
        return False

    if len(value) < 2 or len(value) > 100:
        return False

    if len(value.split()) > 12:
        return False

    if value in _OBVIOUS_NON_INSTITUTION_VALUES:
        return False

    if _URL_PATTERN.search(
        value,
    ):
        return False

    if _SOCIAL_HANDLE_PATTERN.fullmatch(
        value,
    ):
        return False

    if any(value.startswith(prefix) for prefix in _EMPLOYMENT_PREFIXES):
        return False

    return any(character.isalpha() for character in value)


def _extract_institution_values(
    text: str,
) -> tuple[str, ...]:
    """Extract and deduplicate explicit education institution values."""

    patterns = (
        _ENGLISH_STUDENT_AT_PATTERN,
        _ENGLISH_STUDYING_AT_PATTERN,
        _ENGLISH_GRADUATE_OF_PATTERN,
        _ENGLISH_EDUCATED_AT_PATTERN,
        _PERSIAN_STUDENT_OF_PATTERN,
        _PERSIAN_STUDYING_AT_PATTERN,
        _PERSIAN_GRADUATE_OF_PATTERN,
        _PERSIAN_EDUCATED_AT_PATTERN,
    )

    values: list[str] = []

    for pattern in patterns:
        for match in pattern.finditer(
            text,
        ):
            raw_candidate = normalize_text(
                match.group(
                    "institution",
                )
            ).strip()

            if _SOCIAL_HANDLE_PATTERN.fullmatch(
                raw_candidate,
            ):
                continue

            candidate = _clean_institution_value(
                raw_candidate,
            )

            if not _is_valid_institution_value(
                candidate,
            ):
                continue

            if candidate in values:
                continue

            values.append(
                candidate,
            )

    return tuple(
        values,
    )


# ============================================================
# EXTRACTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class BioInstitutionExtractor:
    """
    Extract explicit education-institution claims from public biography text.

    The extractor is deliberately relation-based and open-set.

    Accepted semantics include current or historical education affiliation:
    - ``Student at Tehran University``
    - ``Studying at MIT``
    - ``Graduate of University of Tehran``
    - ``دانشجوی دانشگاه تهران``
    - ``فارغ التحصیل دانشگاه شریف``

    Historical education remains a valid institution fact because
    ``INSTITUTION`` represents explicit educational affiliation, not only
    current enrollment.

    Employment affiliation is intentionally handled elsewhere and does not
    become education evidence merely because an employer is a university.

    This extractor emits Evidence only. Fact resolution belongs to the generic
    FactResolver and application integration is performed separately.
    """

    confidence: float = 0.97

    def __post_init__(self) -> None:
        """Validate extractor configuration."""

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "institution extractor confidence must be between 0 and 1.",
            )

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit education institution evidence."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        values = _extract_institution_values(
            normalized,
        )

        return tuple(
            Evidence(
                source=EvidenceSource.BIO,
                raw_value=bio,
                normalized_value=value,
                confidence=self.confidence,
                extractor="bio_institution_explicit",
                nature=EvidenceNature.EXPLICIT,
                strength=EvidenceStrength.VERY_STRONG,
            )
            for value in values
        )
