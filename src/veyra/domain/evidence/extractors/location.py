"""Explicit multilingual location extraction."""

import re
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

from ..entities import Evidence
from ..enums import (
    EvidenceSource,
    FactKind,
)

_EXPLICIT_LOCATION_PREFIXES = (
    # English
    r"\bbased\s+in\s+",
    r"\bliving\s+in\s+",
    r"\blive\s+in\s+",
    r"\bfrom\s+",
    r"\blocated\s+in\s+",
    r"\blocation\s*:\s*",
    # Persian
    r"ساکن\s+",
    r"ساکنِ\s+",
    r"اهل\s+",
    r"مقیم\s+",
    r"زندگی\s+در\s+",
    r"محل\s+زندگی\s*:?\s*",
)

_PIN_PREFIX = r"(?:📍|🌍|🌎|🌏)\s*"


_NEGATIVE_OR_NON_CURRENT_PREFIXES = (
    # English
    r"\bnot\s+(?:in|from|based\s+in|living\s+in)\s+",
    r"\bformerly\s+(?:in|based\s+in|living\s+in)\s+",
    r"\bused\s+to\s+live\s+in\s+",
    r"\bvisited\s+",
    r"\bvisiting\s+",
    r"\btravel(?:ing|ling)?\s+to\s+",
    r"\btrip\s+to\s+",
    # Persian
    r"ساکن\s+.+\s+نیستم",
    r"دیگر\s+ساکن\s+",
    r"قبلا\s+ساکن\s+",
    r"قبلاً\s+ساکن\s+",
    r"قبلا\s+در\s+.+\s+زندگی",
    r"قبلاً\s+در\s+.+\s+زندگی",
    r"سفر\s+به\s+",
    r"مسافرت\s+به\s+",
)


def _alias_pattern(
    alias: str,
) -> str:
    """
    Build a Unicode-safe alias regex.

    ``re.escape`` prevents aliases from changing regex semantics.
    Loose whitespace allows normalized multi-word aliases.
    """

    escaped = re.escape(
        normalize_text(
            alias,
        )
    )

    return escaped.replace(
        r"\ ",
        r"\s+",
    )


def _matches_non_current_context(
    text: str,
    entity: LocationEntity,
) -> bool:
    """Return whether an entity mention only appears in blocked context."""

    for alias in entity.aliases:
        alias_pattern = _alias_pattern(
            alias,
        )

        for prefix in _NEGATIVE_OR_NON_CURRENT_PREFIXES:
            pattern = re.compile(
                rf"{prefix}{alias_pattern}",
                re.IGNORECASE,
            )

            if pattern.search(text):
                return True

    return False


def _matches_explicit_context(
    text: str,
    entity: LocationEntity,
) -> bool:
    """Return whether one entity appears as an explicit current location."""

    for alias in entity.aliases:
        alias_pattern = _alias_pattern(
            alias,
        )

        explicit_patterns = (
            *(rf"{prefix}{alias_pattern}" for prefix in _EXPLICIT_LOCATION_PREFIXES),
            rf"{_PIN_PREFIX}{alias_pattern}",
        )

        for raw_pattern in explicit_patterns:
            pattern = re.compile(
                raw_pattern,
                re.IGNORECASE,
            )

            if pattern.search(text):
                return True

    return False


def _matches_compact_location_pair(
    text: str,
    entity: LocationEntity,
    *,
    lexicon: LocationLexicon,
) -> bool:
    """
    Detect compact public-profile location forms such as:

    - Tehran, Iran
    - تهران، ایران
    - Tehran | Iran

    This pattern is useful because bios commonly omit prose around location.
    """

    separators = r"\s*(?:,|،|\||/|·|•|-)\s*"

    if entity.kind is LocationEntityKind.CITY:
        countries = lexicon.by_kind(
            LocationEntityKind.COUNTRY,
        )

        for city_alias in entity.aliases:
            city_pattern = _alias_pattern(
                city_alias,
            )

            for country in countries:
                if entity.country_code is not None and country.country_code != entity.country_code:
                    continue

                for country_alias in country.aliases:
                    country_pattern = _alias_pattern(
                        country_alias,
                    )

                    patterns = (
                        rf"{city_pattern}{separators}{country_pattern}",
                        rf"{country_pattern}{separators}{city_pattern}",
                    )

                    if any(
                        re.search(
                            pattern,
                            text,
                            re.IGNORECASE,
                        )
                        for pattern in patterns
                    ):
                        return True

    if entity.kind is LocationEntityKind.COUNTRY:
        cities = lexicon.by_kind(
            LocationEntityKind.CITY,
        )

        for country_alias in entity.aliases:
            country_pattern = _alias_pattern(
                country_alias,
            )

            for city in cities:
                if entity.country_code is not None and city.country_code != entity.country_code:
                    continue

                for city_alias in city.aliases:
                    city_pattern = _alias_pattern(
                        city_alias,
                    )

                    patterns = (
                        rf"{city_pattern}{separators}{country_pattern}",
                        rf"{country_pattern}{separators}{city_pattern}",
                    )

                    if any(
                        re.search(
                            pattern,
                            text,
                            re.IGNORECASE,
                        )
                        for pattern in patterns
                    ):
                        return True

    return False


@dataclass(frozen=True, slots=True)
class BioLocationExtractor:
    """
    Extract explicit current location claims from public biography text.

    This extractor intentionally remains conservative.

    It accepts:
    - explicit location prose
    - location-pin forms
    - compact city/country pairs

    It rejects:
    - travel mentions
    - historical locations
    - negated current-location claims

    Contextual geographic mentions are handled later by the location signal
    pipeline and must not become facts here.
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
        """Extract explicit city and country evidence from one biography."""

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
        """Extract only evidence relevant to CITY or COUNTRY fact resolution."""

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

        if _matches_non_current_context(
            text,
            entity,
        ):
            return None

        if _matches_explicit_context(
            text,
            entity,
        ):
            return (
                self.explicit_confidence,
                "bio_location_explicit",
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
