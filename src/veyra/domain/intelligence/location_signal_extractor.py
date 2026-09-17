"""Multilingual contextual location-signal extraction."""

import re
from dataclasses import dataclass

from .enums import LocationSignalKind
from .location import (
    DEFAULT_LOCATION_LEXICON,
    LocationEntity,
    LocationEntityKind,
    LocationLexicon,
)
from .location_signals import LocationSignal
from .text import normalize_text

_BLOCKED_CONTEXT_PATTERNS = (
    # English travel / historical context.
    r"\bvisited\s+{alias}",
    r"\bvisiting\s+{alias}",
    r"\btravel(?:ing|ling)?\s+to\s+{alias}",
    r"\btrip\s+to\s+{alias}",
    r"\bformerly\s+(?:in|based\s+in|living\s+in)\s+{alias}",
    r"\bused\s+to\s+live\s+in\s+{alias}",
    # Persian travel / historical context.
    r"سفر\s+به\s+{alias}",
    r"مسافرت\s+به\s+{alias}",
    r"قبلا\s+ساکن\s+{alias}",
    r"قبلاً\s+ساکن\s+{alias}",
)

_EXPLICIT_CONTEXT_PATTERNS = (
    # English explicit current-location forms.
    r"\bbased\s+in\s+{alias}",
    r"\bliving\s+in\s+{alias}",
    r"\blive\s+in\s+{alias}",
    r"\bfrom\s+{alias}",
    r"\blocated\s+in\s+{alias}",
    # Persian explicit forms.
    r"ساکن\s+{alias}",
    r"ساکنِ\s+{alias}",
    r"اهل\s+{alias}",
    r"مقیم\s+{alias}",
    r"زندگی\s+در\s+{alias}",
    # Pin forms are explicit location evidence.
    r"(?:📍|🌍|🌎|🌏)\s*{alias}",
)


def _alias_pattern(
    alias: str,
) -> str:
    """Build a safe Unicode-aware regex fragment for one alias."""

    escaped = re.escape(
        normalize_text(
            alias,
        )
    )

    return escaped.replace(
        r"\ ",
        r"\s+",
    )


def _contains_pattern(
    text: str,
    *,
    alias: str,
    patterns: tuple[str, ...],
) -> bool:
    """Return whether one alias matches any contextual pattern."""

    alias_pattern = _alias_pattern(
        alias,
    )

    return any(
        re.search(
            pattern.format(
                alias=alias_pattern,
            ),
            text,
            re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


def _contains_alias(
    text: str,
    alias: str,
) -> bool:
    """Return whether normalized text contains one location alias."""

    alias_pattern = _alias_pattern(
        alias,
    )

    return (
        re.search(
            alias_pattern,
            text,
            re.IGNORECASE,
        )
        is not None
    )


@dataclass(frozen=True, slots=True)
class BioLocationSignalExtractor:
    """
    Extract contextual city signals from public biography text.

    This extractor intentionally does not produce facts.

    Explicit current-location forms are handled by ``BioLocationExtractor``.
    Travel and historical mentions are ignored.

    Examples accepted:
    - "I love Tehran food"
    - "تهران و قهوه"
    - "Designer | Tehran"

    Examples ignored:
    - "Based in Tehran"
    - "ساکن تهران"
    - "Traveling to Tehran"
    - "سفر به تهران"
    """

    lexicon: LocationLexicon = DEFAULT_LOCATION_LEXICON

    weight: float = 0.35
    confidence: float = 0.85

    def __post_init__(self) -> None:
        """Validate signal configuration."""

        if not 0 <= self.weight <= 1:
            raise ValueError(
                "bio location signal weight must be between 0 and 1.",
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "bio location signal confidence must be between 0 and 1.",
            )

    def extract(
        self,
        bio: str,
    ) -> tuple[LocationSignal, ...]:
        """Extract contextual city mentions from one biography."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        signals: list[LocationSignal] = []

        for entity in self.lexicon.by_kind(
            LocationEntityKind.CITY,
        ):
            if not self._is_contextual_match(
                normalized,
                entity,
            ):
                continue

            signals.append(
                LocationSignal(
                    kind=LocationSignalKind.BIO_MENTION,
                    value=entity.value,
                    weight=self.weight,
                    confidence=self.confidence,
                    context=bio,
                )
            )

        return tuple(
            signals,
        )

    @staticmethod
    def _is_contextual_match(
        text: str,
        entity: LocationEntity,
    ) -> bool:
        """
        Return whether a city appears only as usable contextual evidence.

        Explicit, historical, and travel contexts are excluded.
        """

        for alias in entity.aliases:
            if not _contains_alias(
                text,
                alias,
            ):
                continue

            if _contains_pattern(
                text,
                alias=alias,
                patterns=_BLOCKED_CONTEXT_PATTERNS,
            ):
                continue

            if _contains_pattern(
                text,
                alias=alias,
                patterns=_EXPLICIT_CONTEXT_PATTERNS,
            ):
                continue

            return True

        return False
