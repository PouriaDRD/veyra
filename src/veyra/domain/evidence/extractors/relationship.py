"""Explicit relationship-status evidence extraction."""

import re
from dataclasses import dataclass

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    RelationshipStatus,
    normalize_text,
)

from ..entities import Evidence
from ..enums import EvidenceSource

# ============================================================
# REGEX HELPERS
# ============================================================

_EN_WORD = r"[a-z0-9_]"
_FA_WORD = r"[\u0600-\u06ff0-9_]"


def _english_word(
    value: str,
) -> re.Pattern[str]:
    """Build a case-insensitive standalone English word pattern."""

    return re.compile(
        rf"(?<!{_EN_WORD}){value}(?!{_EN_WORD})",
        re.IGNORECASE,
    )


def _persian_word(
    value: str,
) -> re.Pattern[str]:
    """Build a standalone Persian word or phrase pattern."""

    return re.compile(rf"(?<!{_FA_WORD}){value}(?!{_FA_WORD})")


# ============================================================
# POSITIVE STATUS PATTERNS
# ============================================================

_MARRIED_PATTERNS = (
    _english_word("married"),
    _persian_word("متاهل"),
    _persian_word("متأهل"),
)

_SINGLE_PATTERNS = (
    _english_word("single"),
    _persian_word("مجرد"),
)

_ENGAGED_PATTERNS = (
    _english_word("engaged"),
    _persian_word("نامزد"),
)

_IN_RELATIONSHIP_PATTERNS = (
    re.compile(
        r"\bin\s+(?:a\s+)?relationship\b",
        re.IGNORECASE,
    ),
    _persian_word(r"در\s+رابطه"),
)

_DIVORCED_PATTERNS = (
    _english_word("divorced"),
    _persian_word("مطلقه"),
    _persian_word(r"طلاق\s+گرفته"),
)

_WIDOWED_PATTERNS = (
    _english_word("widowed"),
    _english_word("widow"),
    _english_word("widower"),
    _persian_word("بیوه"),
)


# ============================================================
# NEGATION PATTERNS
# ============================================================

_NEGATED_MARRIED_PATTERNS = (
    re.compile(
        r"\bnot\s+married\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bnever\s+married\b",
        re.IGNORECASE,
    ),
    _persian_word(r"(?:متاهل|متأهل)\s+نیستم"),
    _persian_word(r"(?:متاهل|متأهل)\s+نیست"),
    _persian_word(r"(?:متاهل|متأهل)\s+نیستم"),
)

_NEGATED_SINGLE_PATTERNS = (
    re.compile(
        r"\bnot\s+single\b",
        re.IGNORECASE,
    ),
    _persian_word(r"مجرد\s+نیستم"),
    _persian_word(r"مجرد\s+نیست"),
)

_NEGATED_ENGAGED_PATTERNS = (
    re.compile(
        r"\bnot\s+engaged\b",
        re.IGNORECASE,
    ),
    _persian_word(r"نامزد\s+نیستم"),
    _persian_word(r"نامزد\s+نیست"),
)

_NEGATED_RELATIONSHIP_PATTERNS = (
    re.compile(
        r"\bnot\s+in\s+(?:a\s+)?relationship\b",
        re.IGNORECASE,
    ),
    _persian_word(r"در\s+رابطه\s+نیستم"),
    _persian_word(r"در\s+رابطه\s+نیست"),
)


# ============================================================
# HISTORICAL / NON-CURRENT CONTEXT
# ============================================================

_HISTORICAL_MARRIED_PATTERNS = (
    re.compile(
        r"\bformerly\s+married\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bpreviously\s+married\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bused\s+to\s+be\s+married\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwas\s+married\b",
        re.IGNORECASE,
    ),
    _persian_word(r"قبلا\s+(?:متاهل|متأهل)\s+بودم"),
    _persian_word(r"قبلاً\s+(?:متاهل|متأهل)\s+بودم"),
    _persian_word(r"(?:متاهل|متأهل)\s+بودم"),
)

_HISTORICAL_SINGLE_PATTERNS = (
    re.compile(
        r"\bformerly\s+single\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bpreviously\s+single\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bused\s+to\s+be\s+single\b",
        re.IGNORECASE,
    ),
    _persian_word(r"قبلا\s+مجرد\s+بودم"),
    _persian_word(r"قبلاً\s+مجرد\s+بودم"),
    _persian_word(r"مجرد\s+بودم"),
)


# ============================================================
# METAPHORICAL / FALSE-POSITIVE CONTEXT
# ============================================================

_METAPHORICAL_MARRIED_PATTERNS = (
    re.compile(
        r"\bmarried\s+to\s+(?:my\s+)?(?:work|job|career|music|art|coffee|gym|code|coding|business|game|gaming)\b",
        re.IGNORECASE,
    ),
)

_FALSE_SINGLE_PATTERNS = (
    re.compile(
        r"\bsingle\s+(?:malt|page|origin|player|thread|file|line|core|use|purpose|source|family|room|bed)\b",
        re.IGNORECASE,
    ),
)


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _matches_any(
    value: str,
    patterns: tuple[re.Pattern[str], ...],
) -> bool:
    """Return whether any pattern matches."""

    return any(pattern.search(value) for pattern in patterns)


def _is_valid_current_claim(
    *,
    text: str,
    positive_patterns: tuple[re.Pattern[str], ...],
    negative_patterns: tuple[re.Pattern[str], ...] = (),
    historical_patterns: tuple[re.Pattern[str], ...] = (),
    excluded_patterns: tuple[re.Pattern[str], ...] = (),
) -> bool:
    """
    Return whether text contains a valid current explicit claim.

    A positive match is rejected when the same text contains an explicit
    negation, historical statement, or known metaphorical false-positive
    construction.
    """

    if not _matches_any(
        text,
        positive_patterns,
    ):
        return False

    if _matches_any(
        text,
        negative_patterns,
    ):
        return False

    if _matches_any(
        text,
        historical_patterns,
    ):
        return False

    return not _matches_any(
        text,
        excluded_patterns,
    )


@dataclass(frozen=True, slots=True)
class BioRelationshipStatusExtractor:
    """
    Extract explicit current relationship-status claims from public bio text.

    Important rules:
    - explicit positive statements may become factual evidence
    - negated statements do not become opposite facts automatically
    - historical statements do not describe current status
    - metaphorical statements are ignored
    - emoji-only signals are handled separately by intelligence signal
      extractors and never become explicit relationship facts
    """

    confidence: float = 0.98

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit relationship-status claims."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        detected: list[RelationshipStatus] = []

        if _is_valid_current_claim(
            text=normalized,
            positive_patterns=_MARRIED_PATTERNS,
            negative_patterns=_NEGATED_MARRIED_PATTERNS,
            historical_patterns=_HISTORICAL_MARRIED_PATTERNS,
            excluded_patterns=_METAPHORICAL_MARRIED_PATTERNS,
        ):
            detected.append(RelationshipStatus.MARRIED)

        if _is_valid_current_claim(
            text=normalized,
            positive_patterns=_SINGLE_PATTERNS,
            negative_patterns=_NEGATED_SINGLE_PATTERNS,
            historical_patterns=_HISTORICAL_SINGLE_PATTERNS,
            excluded_patterns=_FALSE_SINGLE_PATTERNS,
        ):
            detected.append(RelationshipStatus.SINGLE)

        if _is_valid_current_claim(
            text=normalized,
            positive_patterns=_ENGAGED_PATTERNS,
            negative_patterns=_NEGATED_ENGAGED_PATTERNS,
        ):
            detected.append(RelationshipStatus.ENGAGED)

        if _is_valid_current_claim(
            text=normalized,
            positive_patterns=_IN_RELATIONSHIP_PATTERNS,
            negative_patterns=_NEGATED_RELATIONSHIP_PATTERNS,
        ):
            detected.append(RelationshipStatus.IN_RELATIONSHIP)

        if _matches_any(
            normalized,
            _DIVORCED_PATTERNS,
        ):
            detected.append(RelationshipStatus.DIVORCED)

        if _matches_any(
            normalized,
            _WIDOWED_PATTERNS,
        ):
            detected.append(RelationshipStatus.WIDOWED)

        return tuple(
            Evidence(
                source=EvidenceSource.BIO,
                raw_value=bio,
                normalized_value=status.value,
                confidence=self.confidence,
                extractor="bio_relationship_status_explicit",
                nature=EvidenceNature.EXPLICIT,
                strength=EvidenceStrength.VERY_STRONG,
            )
            for status in detected
        )
