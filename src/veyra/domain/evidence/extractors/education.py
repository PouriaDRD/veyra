"""Explicit education and institution evidence extraction."""

import re
from dataclasses import dataclass
from enum import StrEnum

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    normalize_text,
)

from ..entities import Evidence
from ..enums import EvidenceSource

# ============================================================
# SHARED TEXT BOUNDARIES
# ============================================================


_STOP_CHARS = r"\n|•;,،"
_INSTITUTION_VALUE = r"(?P<institution>[^\n|•;,،]{2,100}?)"
_EDUCATION_FIELD_VALUE = r"(?P<field>[^\n|•;,،]{2,100}?)"


# ============================================================
# EDUCATION VALUE MODEL
# ============================================================


class EducationLevel(StrEnum):
    """Canonical explicit education levels."""

    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"


@dataclass(frozen=True, slots=True)
class EducationCredential:
    """
    Canonical explicit education credential.

    ``field`` remains normalized source-language text. Veyra deliberately does
    not translate fields because translation would introduce a separate
    inference layer.
    """

    level: EducationLevel
    field: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the optional field."""

        if self.field is None:
            return

        normalized_field = normalize_text(
            self.field,
        ).strip(" .:-/")

        if not normalized_field:
            object.__setattr__(
                self,
                "field",
                None,
            )
            return

        object.__setattr__(
            self,
            "field",
            normalized_field,
        )

    @property
    def value(self) -> str:
        """Return deterministic fact value used by Evidence/Fact."""

        if self.field is None:
            return self.level.value

        return f"{self.level.value}:{self.field}"


@dataclass(frozen=True, slots=True)
class _EducationMatch:
    """Internal education match with source span."""

    credential: EducationCredential
    start: int
    end: int

    @property
    def length(self) -> int:
        """Return matched text span length."""

        return self.end - self.start

    def overlaps(
        self,
        other: "_EducationMatch",
    ) -> bool:
        """Return whether two matches overlap in source text."""

        return self.start < other.end and other.start < self.end


# ============================================================
# EDUCATION DEGREE PATTERNS
# ============================================================


_ENGLISH_EDUCATION_PATTERNS: tuple[
    tuple[EducationLevel, re.Pattern[str]],
    ...,
] = (
    (
        EducationLevel.DOCTORATE,
        re.compile(
            rf"\b(?:ph\.?\s*d\.?|doctorate|doctoral degree)"
            rf"(?:\s+(?:in|of))?\s+{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
            re.IGNORECASE,
        ),
    ),
    (
        EducationLevel.MASTER,
        re.compile(
            rf"\b(?:m\.?\s*sc\.?|m\.?\s*s\.?|m\.?\s*a\.?|master'?s?|master degree)"
            rf"(?:\s+(?:in|of))?\s+{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
            re.IGNORECASE,
        ),
    ),
    (
        EducationLevel.BACHELOR,
        re.compile(
            rf"\b(?:b\.?\s*sc\.?|b\.?\s*s\.?|b\.?\s*a\.?|bachelor'?s?|bachelor degree)"
            rf"(?:\s+(?:in|of))?\s+{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
            re.IGNORECASE,
        ),
    ),
    (
        EducationLevel.ASSOCIATE,
        re.compile(
            rf"\b(?:associate degree|associate'?s?)"
            rf"(?:\s+(?:in|of))?\s+{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
            re.IGNORECASE,
        ),
    ),
)

_PERSIAN_EDUCATION_PATTERNS: tuple[
    tuple[EducationLevel, re.Pattern[str]],
    ...,
] = (
    (
        EducationLevel.DOCTORATE,
        re.compile(
            rf"(?:دکتری|دکترا)\s+(?:رشته\s+)?{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
        ),
    ),
    (
        EducationLevel.MASTER,
        re.compile(
            rf"(?:کارشناسی\s+ارشد|فوق\s+لیسانس)"
            rf"\s+(?:رشته\s+)?{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
        ),
    ),
    (
        EducationLevel.BACHELOR,
        re.compile(
            rf"(?<!فوق\s)(?:کارشناسی(?!\s+ارشد)|لیسانس)"
            rf"\s+(?:رشته\s+)?{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
        ),
    ),
    (
        EducationLevel.ASSOCIATE,
        re.compile(
            rf"(?:کاردانی|فوق\s+دیپلم)\s+(?:رشته\s+)?{_EDUCATION_FIELD_VALUE}"
            rf"(?=$|[{_STOP_CHARS}])",
        ),
    ),
)


_FIELD_TRAILING_INSTITUTION_EN = re.compile(
    r"\s+(?:at|from)\s+.+$",
    re.IGNORECASE,
)

_FIELD_TRAILING_INSTITUTION_FA = re.compile(
    r"\s+(?:در|از)\s+(?:دانشگاه|دانشکده|موسسه|مؤسسه)\s+.+$",
)

_FIELD_LEADING_CONNECTOR = re.compile(
    r"^(?:in|of)\s+",
    re.IGNORECASE,
)

_FIELD_NOISE_VALUES = frozenset(
    {
        "student",
        "graduate",
        "degree",
        "دانشجو",
        "فارغ التحصیل",
        "فارغ‌التحصیل",
        "مدرک",
    }
)


def _clean_education_field(
    field: str,
) -> str:
    """Normalize an explicit education field without inferring translation."""

    normalized = normalize_text(
        field,
    ).strip(" .:-/")

    normalized = _FIELD_LEADING_CONNECTOR.sub(
        "",
        normalized,
    )

    normalized = _FIELD_TRAILING_INSTITUTION_EN.sub(
        "",
        normalized,
    )

    normalized = _FIELD_TRAILING_INSTITUTION_FA.sub(
        "",
        normalized,
    )

    return normalized.strip(" .:-/")


def _is_valid_education_field(
    field: str,
) -> bool:
    """Return whether a captured field is meaningful explicit text."""

    if not field:
        return False

    if len(field) > 100:
        return False

    if len(field.split()) > 12:
        return False

    if field in _FIELD_NOISE_VALUES:
        return False

    return any(character.isalpha() for character in field)


def _select_specific_education_matches(
    matches: tuple[_EducationMatch, ...],
) -> tuple[_EducationMatch, ...]:
    """
    Keep only the most specific non-overlapping education matches.

    Longer source spans win. This prevents compound Persian levels such as
    ``کارشناسی ارشد`` and ``فوق لیسانس`` from also producing bachelor matches.
    """

    selected: list[_EducationMatch] = []

    for candidate in sorted(
        matches,
        key=lambda item: (
            -item.length,
            item.start,
            item.end,
            item.credential.value,
        ),
    ):
        if any(candidate.overlaps(existing) for existing in selected):
            continue

        selected.append(
            candidate,
        )

    return tuple(
        sorted(
            selected,
            key=lambda item: (
                item.start,
                item.end,
                item.credential.value,
            ),
        )
    )


def _extract_education_credentials(
    text: str,
) -> tuple[EducationCredential, ...]:
    """Extract deterministic explicit education credentials."""

    matches: list[_EducationMatch] = []

    for level, pattern in (
        *_ENGLISH_EDUCATION_PATTERNS,
        *_PERSIAN_EDUCATION_PATTERNS,
    ):
        for match in pattern.finditer(
            text,
        ):
            field = _clean_education_field(
                match.group(
                    "field",
                )
            )

            if not _is_valid_education_field(
                field,
            ):
                continue

            matches.append(
                _EducationMatch(
                    credential=EducationCredential(
                        level=level,
                        field=field,
                    ),
                    start=match.start(),
                    end=match.end(),
                )
            )

    credentials: list[EducationCredential] = []

    for selected_match in _select_specific_education_matches(
        tuple(
            matches,
        )
    ):
        if selected_match.credential in credentials:
            continue

        credentials.append(
            selected_match.credential,
        )

    return tuple(
        credentials,
    )


# ============================================================
# INSTITUTION RELATION PATTERNS
# ============================================================


_ENGLISH_STUDENT_AT_PATTERN = re.compile(
    rf"\b(?:student|undergraduate|postgraduate|phd student|doctoral student)"
    rf"\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_STUDYING_AT_PATTERN = re.compile(
    rf"\b(?:studying|study)\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_GRADUATE_OF_PATTERN = re.compile(
    rf"\b(?:graduate|alumnus|alumna|alumni)\s+of\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_EDUCATED_AT_PATTERN = re.compile(
    rf"\beducated\s+at\s+{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
    re.IGNORECASE,
)

_PERSIAN_STUDENT_OF_PATTERN = re.compile(
    rf"(?:دانشجو|دانشجوی)\s+(?:در\s+)?{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
)

_PERSIAN_STUDYING_AT_PATTERN = re.compile(
    rf"(?:در\s+حال\s+تحصیل|مشغول\s+به\s+تحصیل)\s+"
    rf"(?:در\s+)?{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
)

_PERSIAN_GRADUATE_OF_PATTERN = re.compile(
    rf"(?:فارغ\s+التحصیل|فارغ‌التحصیل)\s+(?:از\s+)?"
    rf"{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
)

_PERSIAN_EDUCATED_AT_PATTERN = re.compile(
    rf"(?:تحصیل\s+در|تحصیل\s+کرده\s+در)\s+"
    rf"{_INSTITUTION_VALUE}"
    rf"(?=$|[{_STOP_CHARS}])",
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
# EXTRACTORS
# ============================================================


@dataclass(frozen=True, slots=True)
class BioEducationExtractor:
    """
    Extract explicit degree-level and field claims from biography text.

    The extractor requires a recognizable education level. Plain subjects,
    occupations, institutions, and generic student claims do not create
    EDUCATION evidence.

    Field text remains in its source language and is not translated.
    """

    confidence: float = 0.97

    def __post_init__(self) -> None:
        """Validate extractor configuration."""

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "education extractor confidence must be between 0 and 1.",
            )

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit education credential evidence."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        credentials = _extract_education_credentials(
            normalized,
        )

        return tuple(
            Evidence(
                source=EvidenceSource.BIO,
                raw_value=bio,
                normalized_value=credential.value,
                confidence=self.confidence,
                extractor="bio_education_explicit",
                nature=EvidenceNature.EXPLICIT,
                strength=EvidenceStrength.VERY_STRONG,
            )
            for credential in credentials
        )


@dataclass(frozen=True, slots=True)
class BioInstitutionExtractor:
    """
    Extract explicit education-institution claims from public biography text.

    The extractor is deliberately relation-based and open-set.

    Historical education remains a valid institution fact because
    ``INSTITUTION`` represents explicit educational affiliation, not only
    current enrollment.
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
