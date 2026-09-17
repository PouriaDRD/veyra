"""Explicit self-declared gender evidence extraction for Iranian profiles."""

import re
from dataclasses import dataclass

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    normalize_text,
)

from ..entities import Evidence
from ..enums import DeclaredGender, EvidenceSource

_SEGMENT_SPLIT_PATTERN = re.compile(r"[\n\r|•·;,،]+")

_FEMALE_STANDALONE_SEGMENTS = frozenset(
    {
        "زن",
        "خانم",
        "بانو",
        "دختر",
        "woman",
        "female",
        "girl",
        "she/her",
    }
)

_MALE_STANDALONE_SEGMENTS = frozenset(
    {
        "مرد",
        "آقا",
        "پسر",
        "man",
        "male",
        "boy",
        "he/him",
    }
)

_FEMALE_FIRST_PERSON_PATTERNS = (
    re.compile(r"\b(?:i\s+am|i['`]?m|im)\s+(?:a\s+)?(?:woman|female|girl)\b"),
    re.compile(
        r"(?:^|\s)من\s+(?:یک\s+|یه\s+)?(?:زن|خانم|بانو|دختر)"
        r"\s+(?:هستم|ام)(?:$|\s)"
    ),
)

_MALE_FIRST_PERSON_PATTERNS = (
    re.compile(r"\b(?:i\s+am|i['`]?m|im)\s+(?:a\s+)?(?:man|male|boy)\b"),
    re.compile(
        r"(?:^|\s)من\s+(?:یک\s+|یه\s+)?(?:مرد|آقا|پسر)"
        r"\s+(?:هستم|ام)(?:$|\s)"
    ),
)

_FEMALE_PRONOUN_PATTERN = re.compile(r"(?<![a-z0-9_])she\s*[/|•·]\s*her(?![a-z0-9_])")
_MALE_PRONOUN_PATTERN = re.compile(r"(?<![a-z0-9_])he\s*[/|•·]\s*him(?![a-z0-9_])")


def _segments(
    value: str,
) -> tuple[str, ...]:
    """Return normalized, non-empty profile-text segments."""

    return tuple(
        normalized
        for raw_segment in _SEGMENT_SPLIT_PATTERN.split(value)
        if (normalized := normalize_text(raw_segment))
    )


def _matches_any(
    value: str,
    patterns: tuple[re.Pattern[str], ...],
) -> bool:
    """Return whether any pattern matches the normalized value."""

    return any(pattern.search(value) for pattern in patterns)


@dataclass(frozen=True, slots=True)
class BioDeclaredGenderExtractor:
    """
    Extract explicit self-declared gender evidence from Iranian-oriented bios.

    Standalone Persian/English self-labels and explicit first-person statements
    are accepted. Ambiguous contextual mentions remain outside this fact.
    """

    confidence: float = 0.99

    def extract(
        self,
        bio: str,
    ) -> tuple[Evidence, ...]:
        """Extract explicit declared-gender evidence from a bio."""

        normalized = normalize_text(
            bio,
        )

        if not normalized:
            return ()

        segments = _segments(
            bio,
        )

        detected: set[DeclaredGender] = set()

        female_detected = (
            _FEMALE_PRONOUN_PATTERN.search(normalized) is not None
            or _matches_any(
                normalized,
                _FEMALE_FIRST_PERSON_PATTERNS,
            )
            or any(segment in _FEMALE_STANDALONE_SEGMENTS for segment in segments)
        )

        male_detected = (
            _MALE_PRONOUN_PATTERN.search(normalized) is not None
            or _matches_any(
                normalized,
                _MALE_FIRST_PERSON_PATTERNS,
            )
            or any(segment in _MALE_STANDALONE_SEGMENTS for segment in segments)
        )

        if female_detected:
            detected.add(
                DeclaredGender.FEMALE,
            )

        if male_detected:
            detected.add(
                DeclaredGender.MALE,
            )

        return tuple(
            Evidence(
                source=EvidenceSource.BIO,
                raw_value=bio,
                normalized_value=gender.value,
                confidence=self.confidence,
                extractor="bio_declared_gender_explicit",
                nature=EvidenceNature.EXPLICIT,
                strength=EvidenceStrength.VERY_STRONG,
            )
            for gender in sorted(
                detected,
                key=lambda item: item.value,
            )
        )
