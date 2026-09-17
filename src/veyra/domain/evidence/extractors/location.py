"""Explicit multilingual current-location extraction."""

from collections.abc import Iterable
from dataclasses import dataclass

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    normalize_text,
)
from veyra.domain.intelligence.location import (
    DEFAULT_LOCATION_LEXICON,
    LocationEntity,
    LocationEntityKind,
    LocationLexicon,
)
from veyra.domain.intelligence.location_text import (
    context_spans_for_alias,
    find_pattern_spans,
    location_alias_pattern,
    overlaps_any,
)

from ..entities import Evidence
from ..enums import (
    EvidenceSource,
    FactKind,
)

_CURRENT_LOCATION_CONTEXTS = (
    # English current residence.
    r"\bbased\s+in\s+{alias}",
    r"\bliving\s+in\s+{alias}",
    r"\blive\s+in\s+{alias}",
    r"\blocated\s+in\s+{alias}",
    r"\blocation\s*:\s*{alias}",
    # Persian current residence.
    r"ساکن\s+{alias}",
    r"ساکنِ\s+{alias}",
    r"مقیم\s+{alias}",
    r"زندگی\s+در\s+{alias}",
    r"محل\s+زندگی\s*:?\s*{alias}",
    # Compact location marker.
    r"(?:📍|🌍|🌎|🌏)\s*{alias}",
)

_BLOCKED_LOCATION_CONTEXTS = (
    # English negative / former / travel.
    r"\bnot\s+(?:in|from|based\s+in|living\s+in)\s+{alias}",
    r"\bformerly\s+(?:in|based\s+in|living\s+in)\s+{alias}",
    r"\bused\s+to\s+live\s+in\s+{alias}",
    r"\bvisited\s+{alias}",
    r"\bvisiting\s+{alias}",
    r"\btravel(?:ing|ling)?\s+to\s+{alias}",
    r"\btrip\s+to\s+{alias}",
    # Origin is intentionally not current residence.
    r"\bfrom\s+{alias}",
    r"\bborn\s+in\s+{alias}",
    # Persian negative / former / travel.
    r"ساکن\s+{alias}\s+نیستم",
    r"دیگر\s+ساکن\s+{alias}",
    r"قبلا\s+ساکن\s+{alias}",
    r"قبلاً\s+ساکن\s+{alias}",
    r"سفر\s+به\s+{alias}",
    r"مسافرت\s+به\s+{alias}",
    # Persian origin.
    r"اهل\s+{alias}",
    r"متولد\s+{alias}",
    r"زاده(?:ی|ٔ)?\s+{alias}",
)

_PAIR_SEPARATOR = r"\s*(?:,|،|\||/|·|•|-)\s*"


def _blocked_spans(
    text: str,
    *,
    alias: str,
) -> tuple[tuple[int, int], ...]:
    """Return non-current context spans for one alias."""

    return context_spans_for_alias(
        text,
        alias=alias,
        context_patterns=_BLOCKED_LOCATION_CONTEXTS,
    )


def _matches_current_explicit_context(
    text: str,
    entity: LocationEntity,
) -> bool:
    """
    Return whether an entity has an unblocked current-location claim.

    Matching is occurrence-aware. A historical/travel occurrence does not
    suppress a separate valid current-location occurrence elsewhere.
    """

    for alias in entity.aliases:
        blocked = _blocked_spans(
            text,
            alias=alias,
        )

        current = context_spans_for_alias(
            text,
            alias=alias,
            context_patterns=_CURRENT_LOCATION_CONTEXTS,
        )

        for span in current:
            if not overlaps_any(
                span,
                blocked,
            ):
                return True

    return False


def _pair_is_blocked(
    text: str,
    *,
    pair_span: tuple[int, int],
    city_alias: str,
    country_alias: str,
) -> bool:
    """Return whether a compact city/country pair occurs in blocked context."""

    blocked = (
        *_blocked_spans(
            text,
            alias=city_alias,
        ),
        *_blocked_spans(
            text,
            alias=country_alias,
        ),
    )

    return overlaps_any(
        pair_span,
        blocked,
    )


def _matches_compact_location_pair(
    text: str,
    entity: LocationEntity,
    *,
    lexicon: LocationLexicon,
) -> bool:
    """
    Detect an unblocked compact city/country location form.

    Examples:
    - Tehran, Iran
    - تهران، ایران
    - Iran | Tehran

    Origin/travel forms such as ``From Tehran, Iran`` do not become current
    location facts.
    """

    cities = lexicon.by_kind(
        LocationEntityKind.CITY,
    )

    countries = lexicon.by_kind(
        LocationEntityKind.COUNTRY,
    )

    for city in cities:
        for country in countries:
            if city.country_code is not None and country.country_code != city.country_code:
                continue

            if entity.kind is LocationEntityKind.CITY and entity.value != city.value:
                continue

            if entity.kind is LocationEntityKind.COUNTRY and entity.value != country.value:
                continue

            for city_alias in city.aliases:
                city_pattern = location_alias_pattern(
                    city_alias,
                )

                for country_alias in country.aliases:
                    country_pattern = location_alias_pattern(
                        country_alias,
                    )

                    patterns = (
                        (
                            rf"{city_pattern}"
                            rf"{_PAIR_SEPARATOR}"
                            rf"{country_pattern}"
                        ),
                        (
                            rf"{country_pattern}"
                            rf"{_PAIR_SEPARATOR}"
                            rf"{city_pattern}"
                        ),
                    )

                    for pattern in patterns:
                        for pair_span in find_pattern_spans(
                            text,
                            pattern,
                        ):
                            if _pair_is_blocked(
                                text,
                                pair_span=pair_span,
                                city_alias=city_alias,
                                country_alias=country_alias,
                            ):
                                continue

                            return True

    return False


@dataclass(frozen=True, slots=True)
class BioLocationExtractor:
    """
    Extract explicit current-location claims from public biography text.

    Current residence/location and geographic origin are deliberately
    different concepts.

    Accepted:
    - "Based in Tehran"
    - "ساکن تهران"
    - location-pin forms
    - compact city/country pairs

    Not treated as current-location facts:
    - "From Shiraz"
    - "اهل شیراز"
    - travel mentions
    - former locations
    - negated locations
    """

    lexicon: LocationLexicon = DEFAULT_LOCATION_LEXICON

    explicit_confidence: float = 0.96
    compact_pair_confidence: float = 0.92

    def __post_init__(self) -> None:
        """Validate extractor confidence configuration."""

        for value in (
            self.explicit_confidence,
            self.compact_pair_confidence,
        ):
            if not 0 <= value <= 1:
                raise ValueError(
                    "location extractor confidence must be between 0 and 1.",
                )

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit current city and country evidence."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        evidence: list[Evidence] = []

        for entity in self.lexicon.entries:
            match = self._classify_match(
                normalized,
                entity,
            )

            if match is None:
                continue

            confidence, extractor_name = match

            evidence.append(
                Evidence(
                    source=EvidenceSource.BIO,
                    raw_value=bio,
                    normalized_value=entity.value,
                    confidence=confidence,
                    extractor=extractor_name,
                    nature=EvidenceNature.EXPLICIT,
                    strength=EvidenceStrength.VERY_STRONG,
                )
            )

        return tuple(
            evidence,
        )

    def extract_for_kind(
        self,
        bio: str,
        *,
        kind: FactKind,
    ) -> tuple[Evidence, ...]:
        """Extract only CITY or COUNTRY current-location evidence."""

        if kind not in {
            FactKind.CITY,
            FactKind.COUNTRY,
        }:
            raise ValueError(
                "location extractor only supports CITY and COUNTRY.",
            )

        allowed_location_kind = (
            LocationEntityKind.CITY if kind is FactKind.CITY else LocationEntityKind.COUNTRY
        )

        allowed_values = {
            entity.value
            for entity in self.lexicon.by_kind(
                allowed_location_kind,
            )
        }

        return tuple(
            item
            for item in self.extract(
                bio,
            )
            if (
                isinstance(
                    item.normalized_value,
                    str,
                )
                and item.normalized_value in allowed_values
            )
        )

    def _classify_match(
        self,
        text: str,
        entity: LocationEntity,
    ) -> (
        tuple[
            float,
            str,
        ]
        | None
    ):
        """Classify one explicit geographic match."""

        if _matches_current_explicit_context(
            text,
            entity,
        ):
            return (
                self.explicit_confidence,
                "bio_location_current",
            )

        if _matches_compact_location_pair(
            text,
            entity,
            lexicon=self.lexicon,
        ):
            return (
                self.compact_pair_confidence,
                "bio_location_pair",
            )

        return None


def location_values(
    entries: Iterable[LocationEntity],
) -> tuple[str, ...]:
    """Return normalized values from location catalog entries."""

    return tuple(entry.value for entry in entries)
