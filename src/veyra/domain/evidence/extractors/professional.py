"""Explicit professional occupation and employer evidence extraction."""

import re
from dataclasses import dataclass
from typing import Literal

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    normalize_text,
)

from ..entities import Evidence
from ..enums import EvidenceSource

OccupationTextSource = Literal[
    "bio",
    "display_name",
]


# ============================================================
# OCCUPATION CATALOG
# ============================================================


@dataclass(frozen=True, slots=True)
class OccupationEntry:
    """
    One canonical occupation and its multilingual public aliases.

    ``value`` is the normalized fact value persisted in Evidence/Fact.

    Aliases are language-facing extraction forms only.
    """

    value: str
    aliases: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and normalize occupation entry."""

        value = normalize_text(
            self.value,
        )

        aliases = tuple(normalize_text(alias) for alias in self.aliases)

        if not value:
            raise ValueError(
                "occupation value must not be empty.",
            )

        if not aliases:
            raise ValueError(
                "occupation aliases must not be empty.",
            )

        if any(not alias for alias in aliases):
            raise ValueError(
                "occupation aliases must not contain empty values.",
            )

        if len(set(aliases)) != len(aliases):
            raise ValueError(
                "occupation aliases must be unique.",
            )

        object.__setattr__(
            self,
            "value",
            value,
        )

        object.__setattr__(
            self,
            "aliases",
            aliases,
        )


@dataclass(frozen=True, slots=True)
class OccupationLexicon:
    """Immutable multilingual occupation catalog."""

    entries: tuple[OccupationEntry, ...]

    def __post_init__(self) -> None:
        """Validate lexicon invariants."""

        if not self.entries:
            raise ValueError(
                "occupation lexicon must not be empty.",
            )

        values = tuple(entry.value for entry in self.entries)

        if len(set(values)) != len(values):
            raise ValueError(
                "occupation values must be unique.",
            )

        seen_aliases: set[str] = set()

        for entry in self.entries:
            for alias in entry.aliases:
                if alias in seen_aliases:
                    raise ValueError(
                        f"duplicate occupation alias: {alias}.",
                    )

                seen_aliases.add(
                    alias,
                )

    def find_by_alias(
        self,
        alias: str,
    ) -> OccupationEntry | None:
        """Return occupation entry matching one normalized alias."""

        normalized = normalize_text(
            alias,
        )

        if not normalized:
            return None

        for entry in self.entries:
            if normalized in entry.aliases:
                return entry

        return None


DEFAULT_OCCUPATION_LEXICON = OccupationLexicon(
    entries=(
        OccupationEntry(
            value="software engineer",
            aliases=(
                "software engineer",
                "مهندس نرم افزار",
            ),
        ),
        OccupationEntry(
            value="software developer",
            aliases=(
                "software developer",
                "developer",
                "توسعه دهنده",
            ),
        ),
        OccupationEntry(
            value="programmer",
            aliases=(
                "programmer",
                "برنامه نویس",
            ),
        ),
        OccupationEntry(
            value="data analyst",
            aliases=(
                "data analyst",
                "تحلیلگر داده",
            ),
        ),
        OccupationEntry(
            value="business analyst",
            aliases=(
                "business analyst",
                "تحلیلگر کسب و کار",
            ),
        ),
        OccupationEntry(
            value="product manager",
            aliases=(
                "product manager",
                "مدیر محصول",
            ),
        ),
        OccupationEntry(
            value="product designer",
            aliases=(
                "product designer",
                "طراح محصول",
            ),
        ),
        OccupationEntry(
            value="graphic designer",
            aliases=(
                "graphic designer",
                "طراح گرافیک",
            ),
        ),
        OccupationEntry(
            value="designer",
            aliases=(
                "designer",
                "طراح",
            ),
        ),
        OccupationEntry(
            value="doctor",
            aliases=(
                "doctor",
                "physician",
                "پزشک",
                "دکتر",
            ),
        ),
        OccupationEntry(
            value="lawyer",
            aliases=(
                "lawyer",
                "attorney",
                "وکیل",
            ),
        ),
        OccupationEntry(
            value="teacher",
            aliases=(
                "teacher",
                "مدرس",
            ),
        ),
        OccupationEntry(
            value="consultant",
            aliases=(
                "consultant",
                "مشاور",
            ),
        ),
        OccupationEntry(
            value="architect",
            aliases=(
                "architect",
                "معمار",
            ),
        ),
        OccupationEntry(
            value="photographer",
            aliases=(
                "photographer",
                "عکاس",
            ),
        ),
    )
)


# ============================================================
# OCCUPATION MATCH MODELS
# ============================================================


@dataclass(frozen=True, slots=True)
class _OccupationMatch:
    """Internal normalized occupation match."""

    entry: OccupationEntry
    alias: str
    start: int
    end: int

    @property
    def span(self) -> tuple[int, int]:
        """Return match span."""

        return (
            self.start,
            self.end,
        )

    @property
    def length(self) -> int:
        """Return matched span length."""

        return self.end - self.start


# ============================================================
# OCCUPATION MATCHING
# ============================================================


def _alias_pattern(
    alias: str,
) -> re.Pattern[str]:
    """Build Unicode-aware whole-alias pattern."""

    normalized = normalize_text(
        alias,
    )

    if not normalized:
        raise ValueError(
            "occupation alias must not be empty.",
        )

    escaped = re.escape(
        normalized,
    ).replace(
        r"\ ",
        r"\s+",
    )

    return re.compile(
        rf"(?<!\w){escaped}(?!\w)",
        re.IGNORECASE,
    )


def _find_entry_matches(
    text: str,
    entry: OccupationEntry,
) -> tuple[_OccupationMatch, ...]:
    """Return all alias matches for one occupation entry."""

    matches: list[_OccupationMatch] = []

    for alias in entry.aliases:
        pattern = _alias_pattern(
            alias,
        )

        for match in pattern.finditer(
            text,
        ):
            matches.append(
                _OccupationMatch(
                    entry=entry,
                    alias=alias,
                    start=match.start(),
                    end=match.end(),
                )
            )

    return tuple(
        matches,
    )


def _spans_overlap(
    first: tuple[int, int],
    second: tuple[int, int],
) -> bool:
    """Return whether two half-open spans overlap."""

    first_start, first_end = first
    second_start, second_end = second

    return first_start < second_end and second_start < first_end


def _select_specific_matches(
    matches: tuple[_OccupationMatch, ...],
) -> tuple[_OccupationMatch, ...]:
    """
    Keep the most specific non-overlapping occupation matches.

    Longer occupation phrases win over generic overlapping phrases.
    """

    ranked = sorted(
        matches,
        key=lambda item: (
            -item.length,
            item.start,
            item.end,
            item.entry.value,
            item.alias,
        ),
    )

    selected: list[_OccupationMatch] = []

    for candidate in ranked:
        if any(
            _spans_overlap(
                candidate.span,
                existing.span,
            )
            for existing in selected
        ):
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
                item.entry.value,
            ),
        )
    )


# ============================================================
# OCCUPATION FALSE-POSITIVE CONTEXT
# ============================================================


_ENGLISH_NON_CURRENT_PATTERNS = (
    re.compile(
        r"\b(?:former|formerly|previously|ex)\s+$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:student|studying|study)\s+(?:as\s+)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:aspiring|future)\s+$",
        re.IGNORECASE,
    ),
)

_PERSIAN_NON_CURRENT_PATTERNS = (
    re.compile(
        r"(?:سابق|قبلا|قبلاً)\s+$",
    ),
    re.compile(
        r"(?:دانشجو|دانشجوی|در حال تحصیل(?:\s+در)?)\s+$",
    ),
    re.compile(
        r"(?:آینده|علاقه مند به|علاقه‌مند به)\s+$",
    ),
)

_ENGLISH_RECRUITING_PATTERNS = (
    re.compile(
        r"\b(?:hiring|hire|looking for|seeking|wanted|need|need a|need an)\s+$",
        re.IGNORECASE,
    ),
)

_PERSIAN_RECRUITING_PATTERNS = (
    re.compile(
        r"(?:استخدام|استخدام می کنیم|استخدام می‌کنیم|به دنبال|دنبال|نیازمند|نیاز به)\s+$",
    ),
)

_ENGLISH_NEGATION_PATTERNS = (
    re.compile(
        r"\b(?:not|not a|not an|never been a)\s+$",
        re.IGNORECASE,
    ),
)

_PERSIAN_NEGATION_PATTERNS = (
    re.compile(
        r"(?:نیستم|نیست|نبودم)\s*$",
    ),
)


def _left_context(
    text: str,
    span: tuple[int, int],
    *,
    size: int = 40,
) -> str:
    """Return normalized text immediately before one match."""

    start, _ = span

    return text[
        max(
            0,
            start - size,
        ) : start
    ]


def _right_context(
    text: str,
    span: tuple[int, int],
    *,
    size: int = 24,
) -> str:
    """Return normalized text immediately after one match."""

    _, end = span

    return text[
        end : min(
            len(text),
            end + size,
        )
    ]


def _matches_any_suffix(
    value: str,
    patterns: tuple[
        re.Pattern[str],
        ...,
    ],
) -> bool:
    """Return whether context ends with any excluded construction."""

    return any(
        pattern.search(
            value,
        )
        is not None
        for pattern in patterns
    )


def _has_non_current_context(
    text: str,
    span: tuple[int, int],
) -> bool:
    """Return whether occupation is historical, aspirational, or educational."""

    left = _left_context(
        text,
        span,
    )

    return _matches_any_suffix(
        left,
        (
            *_ENGLISH_NON_CURRENT_PATTERNS,
            *_PERSIAN_NON_CURRENT_PATTERNS,
        ),
    )


def _has_recruiting_context(
    text: str,
    span: tuple[int, int],
) -> bool:
    """Return whether text is recruiting that occupation."""

    left = _left_context(
        text,
        span,
    )

    return _matches_any_suffix(
        left,
        (
            *_ENGLISH_RECRUITING_PATTERNS,
            *_PERSIAN_RECRUITING_PATTERNS,
        ),
    )


def _has_negated_context(
    text: str,
    span: tuple[int, int],
) -> bool:
    """Return whether occupation claim is explicitly negated."""

    left = _left_context(
        text,
        span,
    )

    if _matches_any_suffix(
        left,
        _ENGLISH_NEGATION_PATTERNS,
    ):
        return True

    right = _right_context(
        text,
        span,
    )

    return any(
        pattern.search(
            right,
        )
        is not None
        for pattern in _PERSIAN_NEGATION_PATTERNS
    )


def _is_valid_current_occupation(
    text: str,
    span: tuple[int, int],
) -> bool:
    """Return whether one role mention may describe current occupation."""

    if _has_non_current_context(
        text,
        span,
    ):
        return False

    if _has_recruiting_context(
        text,
        span,
    ):
        return False

    return not _has_negated_context(
        text,
        span,
    )


# ============================================================
# EMPLOYER EXTRACTION
# ============================================================


_EMPLOYER_STOP_CHARS = r"\n|•;,،"
_EMPLOYER_VALUE = r"(?P<employer>[^\n|•;,،]{2,80}?)"

_ENGLISH_WORKS_AT_PATTERN = re.compile(
    rf"\b(?:i\s+)?(?:work|works|working)\s+at\s+"
    rf"{_EMPLOYER_VALUE}"
    rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
    re.IGNORECASE,
)

_ENGLISH_EMPLOYED_AT_PATTERN = re.compile(
    rf"\b(?:employed|employee)\s+at\s+"
    rf"{_EMPLOYER_VALUE}"
    rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
    re.IGNORECASE,
)

_PERSIAN_WORKS_AT_PATTERN = re.compile(
    rf"(?:در|برای)\s+"
    rf"{_EMPLOYER_VALUE}"
    rf"\s+کار\s+می\s*کنم"
    rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
)

_EMPLOYER_HISTORICAL_PREFIXES = (
    re.compile(
        r"\b(?:former|formerly|previously|used to|worked)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:سابق|قبلا|قبلاً|کار می کردم|کار می‌کردم)",
    ),
)

_EMPLOYER_RECRUITING_PREFIXES = (
    re.compile(
        r"\b(?:hiring|looking for|seeking|recruiting)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:استخدام|به دنبال|نیازمند)",
    ),
)

_EMPLOYER_NEGATED_PREFIXES = (
    re.compile(
        r"\b(?:not|don't|do not|no longer)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:نیستم|نمی کنم|نمی‌کنم|دیگر)",
    ),
)

_INSTITUTION_MARKERS = (
    "university",
    "college",
    "school",
    "institute",
    "academy",
    "دانشگاه",
    "دانشکده",
    "مدرسه",
    "موسسه",
    "مؤسسه",
    "آکادمی",
)

_LOCATION_ONLY_VALUES = frozenset(
    {
        "tehran",
        "iran",
        "london",
        "تهران",
        "ایران",
        "لندن",
    }
)

_COMPANY_LEGAL_SUFFIX_PATTERN = re.compile(
    r"""
    (?:
        [,.\s]+
        (?:
            inc(?:orporated)? |
            ltd |
            limited |
            llc |
            l\.l\.c |
            corp(?:oration)? |
            co(?:mpany)?
        )
        \.?
    )$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_EMPLOYER_URL_PATTERN = re.compile(
    r"(?:https?://|www\.)",
    re.IGNORECASE,
)


def _clean_employer_value(
    value: str,
) -> str:
    """Normalize one employer candidate into a stable public fact value."""

    normalized = normalize_text(
        value,
    )

    normalized = normalized.strip(" .:-/")

    normalized = re.sub(
        r"^(?:the|شرکت)\s+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    normalized = _COMPANY_LEGAL_SUFFIX_PATTERN.sub(
        "",
        normalized,
    )

    return normalized.strip(" .:-/")


def _is_institution_value(
    value: str,
) -> bool:
    """Return whether value appears to describe an educational institution."""

    return any(
        re.search(
            rf"(?<!\w){re.escape(marker)}(?!\w)",
            value,
            re.IGNORECASE,
        )
        is not None
        for marker in _INSTITUTION_MARKERS
    )


def _is_valid_employer_value(
    value: str,
) -> bool:
    """Validate one normalized employer candidate conservatively."""

    if not value:
        return False

    if len(value) < 2 or len(value) > 80:
        return False

    if len(value.split()) > 8:
        return False

    if value.startswith(
        "@",
    ):
        return False

    if _EMPLOYER_URL_PATTERN.search(
        value,
    ):
        return False

    if value in _LOCATION_ONLY_VALUES:
        return False

    if _is_institution_value(
        value,
    ):
        return False

    return any(character.isalpha() for character in value)


def _has_invalid_employer_context(
    text: str,
    match_start: int,
) -> bool:
    """Reject historical, recruiting, and negated employer statements."""

    left = text[
        max(
            0,
            match_start - 48,
        ) : match_start
    ]

    patterns = (
        *_EMPLOYER_HISTORICAL_PREFIXES,
        *_EMPLOYER_RECRUITING_PREFIXES,
        *_EMPLOYER_NEGATED_PREFIXES,
    )

    return any(
        pattern.search(
            left,
        )
        is not None
        for pattern in patterns
    )


def _occupation_employer_patterns(
    lexicon: OccupationLexicon,
) -> tuple[
    re.Pattern[str],
    ...,
]:
    """
    Build explicit occupation-to-employer relation patterns.

    Supported relations:
    - ``Software Engineer at Acme``
    - ``Software Engineer @ Acme``
    - ``مهندس نرم افزار در دیجی کالا``
    - ``مهندس نرم افزار @ دیجی کالا``

    An ``@username`` mention is deliberately not accepted as an employer value.
    """

    patterns: list[re.Pattern[str]] = []

    for entry in lexicon.entries:
        for alias in entry.aliases:
            escaped = re.escape(
                alias,
            ).replace(
                r"\ ",
                r"\s+",
            )

            if re.search(
                r"[\u0600-\u06ff]",
                alias,
            ):
                patterns.extend(
                    (
                        re.compile(
                            rf"(?<!\w){escaped}(?!\w)"
                            rf"\s+در\s+"
                            rf"{_EMPLOYER_VALUE}"
                            rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
                        ),
                        re.compile(
                            rf"(?<!\w){escaped}(?!\w)"
                            rf"\s*@\s*"
                            rf"{_EMPLOYER_VALUE}"
                            rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
                        ),
                    )
                )

            else:
                patterns.extend(
                    (
                        re.compile(
                            rf"(?<!\w){escaped}(?!\w)"
                            rf"\s+at\s+"
                            rf"{_EMPLOYER_VALUE}"
                            rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
                            re.IGNORECASE,
                        ),
                        re.compile(
                            rf"(?<!\w){escaped}(?!\w)"
                            rf"\s*@\s*"
                            rf"{_EMPLOYER_VALUE}"
                            rf"(?=$|[{_EMPLOYER_STOP_CHARS}])",
                            re.IGNORECASE,
                        ),
                    )
                )

    return tuple(
        patterns,
    )


def _extract_employer_candidates(
    text: str,
    *,
    lexicon: OccupationLexicon,
) -> tuple[str, ...]:
    """Extract normalized employer candidates from explicit current claims."""

    patterns = (
        _ENGLISH_WORKS_AT_PATTERN,
        _ENGLISH_EMPLOYED_AT_PATTERN,
        _PERSIAN_WORKS_AT_PATTERN,
        *_occupation_employer_patterns(
            lexicon,
        ),
    )

    values: list[str] = []

    for pattern in patterns:
        for match in pattern.finditer(
            text,
        ):
            if _has_invalid_employer_context(
                text,
                match.start(),
            ):
                continue

            raw_candidate = match.group(
                "employer",
            ).strip()

            if raw_candidate.startswith(
                "@",
            ):
                continue

            candidate = _clean_employer_value(
                raw_candidate,
            )

            if not _is_valid_employer_value(
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
# OCCUPATION EXTRACTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class ProfileOccupationExtractor:
    """
    Extract explicit current occupation claims from public profile text.

    This extractor creates factual Evidence, not profile-purpose signals.

    ``Freelance Developer`` remains valid occupation evidence because
    ``freelance`` describes work mode rather than negating the role.

    The extractor intentionally does not infer employer information.
    """

    lexicon: OccupationLexicon = DEFAULT_OCCUPATION_LEXICON

    bio_confidence: float = 0.96
    display_name_confidence: float = 0.92

    def __post_init__(self) -> None:
        """Validate extractor configuration."""

        for confidence in (
            self.bio_confidence,
            self.display_name_confidence,
        ):
            if not 0 <= confidence <= 1:
                raise ValueError(
                    "occupation extractor confidence must be between 0 and 1.",
                )

    def extract(
        self,
        text: str,
        *,
        source: OccupationTextSource,
    ) -> tuple[Evidence, ...]:
        """Extract explicit occupation Evidence from one profile field."""

        if source not in {
            "bio",
            "display_name",
        }:
            raise ValueError(
                "occupation source must be 'bio' or 'display_name'.",
            )

        normalized = normalize_text(
            text,
        )

        if not normalized:
            return ()

        matches: list[_OccupationMatch] = []

        for entry in self.lexicon.entries:
            matches.extend(
                _find_entry_matches(
                    normalized,
                    entry,
                )
            )

        valid_matches = tuple(
            match
            for match in matches
            if _is_valid_current_occupation(
                normalized,
                match.span,
            )
        )

        selected_matches = _select_specific_matches(
            valid_matches,
        )

        evidence: list[Evidence] = []
        seen_values: set[str] = set()

        for match in selected_matches:
            if match.entry.value in seen_values:
                continue

            evidence.append(
                self._build_evidence(
                    text=text,
                    source=source,
                    entry=match.entry,
                )
            )

            seen_values.add(
                match.entry.value,
            )

        return tuple(
            evidence,
        )

    def _build_evidence(
        self,
        *,
        text: str,
        source: OccupationTextSource,
        entry: OccupationEntry,
    ) -> Evidence:
        """Build one explicit occupation evidence item."""

        if source == "bio":
            evidence_source = EvidenceSource.BIO
            confidence = self.bio_confidence
            extractor = "bio_occupation_explicit"
        else:
            evidence_source = EvidenceSource.DISPLAY_NAME
            confidence = self.display_name_confidence
            extractor = "display_name_occupation_explicit"

        return Evidence(
            source=evidence_source,
            raw_value=text,
            normalized_value=entry.value,
            confidence=confidence,
            extractor=extractor,
            nature=EvidenceNature.EXPLICIT,
            strength=EvidenceStrength.VERY_STRONG,
        )


# ============================================================
# EMPLOYER EXTRACTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class BioEmployerExtractor:
    """
    Extract explicit current employer claims from public biography text.

    Supported examples include:
    - ``Works at Acme``
    - ``Software Engineer at Acme``
    - ``Software Engineer @ Acme``
    - ``مهندس نرم افزار در دیجی کالا``
    - ``مهندس نرم افزار @ دیجی کالا``
    - ``در دیجی کالا کار می کنم``

    Deliberately unsupported as employer facts:
    - founder/co-founder ownership relations
    - freelance/self-employed work
    - consulting relations expressed as ``for``
    - historical employment
    - recruiting statements
    - negated employment
    - educational institutions
    - social ``@username`` mentions

    Employer extraction remains factual and independent from profile-purpose
    inference.
    """

    occupation_lexicon: OccupationLexicon = DEFAULT_OCCUPATION_LEXICON

    confidence: float = 0.96

    def __post_init__(self) -> None:
        """Validate extractor configuration."""

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "employer extractor confidence must be between 0 and 1.",
            )

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit current employer evidence."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        values = _extract_employer_candidates(
            normalized,
            lexicon=self.occupation_lexicon,
        )

        return tuple(
            Evidence(
                source=EvidenceSource.BIO,
                raw_value=bio,
                normalized_value=value,
                confidence=self.confidence,
                extractor="bio_employer_explicit",
                nature=EvidenceNature.EXPLICIT,
                strength=EvidenceStrength.VERY_STRONG,
            )
            for value in values
        )
