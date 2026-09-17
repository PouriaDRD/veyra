"""Multilingual contextual location-signal extraction."""

from dataclasses import dataclass

from .enums import (
    LocationRelation,
    LocationSignalKind,
)
from .location import (
    DEFAULT_LOCATION_LEXICON,
    LocationEntity,
    LocationEntityKind,
    LocationLexicon,
)
from .location_signals import LocationSignal
from .location_text import (
    context_spans_for_alias,
    find_pattern_spans,
    location_alias_pattern,
    overlaps_any,
)
from .text import normalize_text

_BLOCKED_CONTEXTS = (
    # English travel / history / negation.
    r"\bvisited\s+{alias}",
    r"\bvisiting\s+{alias}",
    r"\btravel(?:ing|ling)?\s+to\s+{alias}",
    r"\btrip\s+to\s+{alias}",
    r"\bformerly\s+(?:in|based\s+in|living\s+in)\s+{alias}",
    r"\bused\s+to\s+live\s+in\s+{alias}",
    r"\bnot\s+(?:in|based\s+in|living\s+in)\s+{alias}",
    # Persian travel / history / negation.
    r"سفر\s+به\s+{alias}",
    r"مسافرت\s+به\s+{alias}",
    r"قبلا\s+ساکن\s+{alias}",
    r"قبلاً\s+ساکن\s+{alias}",
    r"دیگر\s+ساکن\s+{alias}",
)

_CURRENT_CONTEXTS = (
    # English.
    r"\bbased\s+in\s+{alias}",
    r"\bliving\s+in\s+{alias}",
    r"\blive\s+in\s+{alias}",
    r"\blocated\s+in\s+{alias}",
    r"\blocation\s*:\s*{alias}",
    # Persian.
    r"ساکن\s+{alias}",
    r"ساکنِ\s+{alias}",
    r"مقیم\s+{alias}",
    r"زندگی\s+در\s+{alias}",
    r"محل\s+زندگی\s*:?\s*{alias}",
    # Explicit profile location markers.
    r"(?:📍|🌍|🌎|🌏)\s*{alias}",
)

_ORIGIN_CONTEXTS = (
    # English.
    r"\bfrom\s+{alias}",
    r"\bborn\s+in\s+{alias}",
    # Persian.
    r"اهل\s+{alias}",
    r"متولد\s+{alias}",
    r"زاده(?:ی|ٔ)?\s+{alias}",
)

_INSTITUTIONAL_CONTEXTS = (
    # English organization names.
    r"{alias}\s+(?:university|college|institute|school|hospital|clinic)\b",
    r"(?:university|college|institute|school|hospital|clinic)" r"\s+(?:of\s+)?{alias}",
    r"{alias}\s+times\b",
    r"{alias}\s+stock\s+exchange\b",
    # Persian organization names.
    r"دانشگاه\s+{alias}",
    r"دانشگاه\s+علوم\s+پزشکی\s+{alias}",
    r"{alias}\s+دانشگاه",
    r"بورس\s+{alias}",
)


@dataclass(frozen=True, slots=True)
class _LocationMentionClassification:
    """Internal semantic classification for one city in biography text."""

    has_current: bool = False
    has_contextual: bool = False
    has_origin: bool = False


@dataclass(frozen=True, slots=True)
class BioLocationSignalExtractor:
    """
    Extract non-factual city signals from public biography text.

    The extractor distinguishes:
    - current residence claims
    - origin/hometown claims
    - contextual mentions
    - travel/history mentions
    - institutional name mentions

    Explicit current residence is intentionally left to
    ``BioLocationExtractor`` to avoid double counting.
    """

    lexicon: LocationLexicon = DEFAULT_LOCATION_LEXICON

    contextual_weight: float = 0.35
    contextual_confidence: float = 0.85

    origin_weight: float = 0.20
    origin_confidence: float = 0.90

    def __post_init__(self) -> None:
        """Validate configured weights and confidence values."""

        values = (
            self.contextual_weight,
            self.contextual_confidence,
            self.origin_weight,
            self.origin_confidence,
        )

        if any(not 0 <= value <= 1 for value in values):
            raise ValueError(
                "location signal weights and confidence must be between 0 and 1.",
            )

    def extract(
        self,
        bio: str,
    ) -> tuple[LocationSignal, ...]:
        """Extract semantic city signals from biography text."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        signals: list[LocationSignal] = []

        for entity in self.lexicon.by_kind(
            LocationEntityKind.CITY,
        ):
            classification = self._classify_entity(
                normalized,
                entity,
            )

            # Explicit current residence already becomes Fact evidence.
            # Emitting another signal here would double count the same source.
            if classification.has_current:
                continue

            if classification.has_contextual:
                signals.append(
                    LocationSignal(
                        kind=LocationSignalKind.BIO_MENTION,
                        value=entity.value,
                        weight=self.contextual_weight,
                        confidence=self.contextual_confidence,
                        relation=LocationRelation.CONTEXTUAL_MENTION,
                        context=bio,
                    )
                )

                continue

            if classification.has_origin:
                signals.append(
                    LocationSignal(
                        kind=LocationSignalKind.BIO_MENTION,
                        value=entity.value,
                        weight=self.origin_weight,
                        confidence=self.origin_confidence,
                        relation=LocationRelation.ORIGIN,
                        context=bio,
                    )
                )

        return tuple(
            signals,
        )

    @staticmethod
    def _classify_entity(
        text: str,
        entity: LocationEntity,
    ) -> _LocationMentionClassification:
        """Classify all occurrences of one city in biography text."""

        has_current = False
        has_contextual = False
        has_origin = False

        for alias in entity.aliases:
            alias_pattern = location_alias_pattern(
                alias,
            )

            alias_spans = find_pattern_spans(
                text,
                alias_pattern,
            )

            if not alias_spans:
                continue

            blocked = context_spans_for_alias(
                text,
                alias=alias,
                context_patterns=_BLOCKED_CONTEXTS,
            )

            current = context_spans_for_alias(
                text,
                alias=alias,
                context_patterns=_CURRENT_CONTEXTS,
            )

            origin = context_spans_for_alias(
                text,
                alias=alias,
                context_patterns=_ORIGIN_CONTEXTS,
            )

            institutional = context_spans_for_alias(
                text,
                alias=alias,
                context_patterns=_INSTITUTIONAL_CONTEXTS,
            )

            for span in alias_spans:
                if overlaps_any(
                    span,
                    blocked,
                ):
                    continue

                if overlaps_any(
                    span,
                    institutional,
                ):
                    continue

                if overlaps_any(
                    span,
                    current,
                ):
                    has_current = True
                    continue

                if overlaps_any(
                    span,
                    origin,
                ):
                    has_origin = True
                    continue

                has_contextual = True

        return _LocationMentionClassification(
            has_current=has_current,
            has_contextual=has_contextual,
            has_origin=has_origin,
        )
