"""Relationship-themed contextual signal extraction."""

import re
from dataclasses import dataclass

from .enums import RelationshipSignalKind
from .relationship import RelationshipSignal
from .text import normalize_text

# ============================================================
# NAME DETECTION
# ============================================================

_LATIN_NAME_TOKEN = r"[A-Za-z]" r"[A-Za-z0-9_.\-]{1,30}"

_PERSIAN_NAME_TOKEN = r"[\u0600-\u06ff]" r"[\u0600-\u06ff0-9_.\-]{1,30}"

_NAME_TOKEN = rf"(?:{_LATIN_NAME_TOKEN}|{_PERSIAN_NAME_TOKEN})"


# ============================================================
# EMOJI DEFINITIONS
# ============================================================

_RING = "💍"

_RED_HEART_VARIANTS = (
    "❤️",
    "❤",
)

_GENERIC_HEARTS = (
    "💕",
    "💖",
    "💗",
    "💓",
    "💞",
    "💘",
    "💝",
    "💟",
)

_DECORATIVE_HEARTS = (
    "🤍",
    "🖤",
    "💙",
    "💚",
    "💛",
    "💜",
    "🩷",
    "🩵",
    "🩶",
    "🤎",
)


# ============================================================
# NAME-ADJACENT SIGNAL PATTERNS
# ============================================================

_NAME_RING_PATTERN = re.compile(
    rf"""
    (?:
        {_NAME_TOKEN}
        \s*
        {_RING}
        |
        {_RING}
        \s*
        {_NAME_TOKEN}
    )
    """,
    re.VERBOSE,
)

_NAME_RED_HEART_PATTERN = re.compile(
    rf"""
    (?:
        {_NAME_TOKEN}
        \s*
        (?:❤️|❤)
        |
        (?:❤️|❤)
        \s*
        {_NAME_TOKEN}
    )
    """,
    re.VERBOSE,
)


# ============================================================
# COMMON NON-NAME FALSE POSITIVES
# ============================================================

_NON_PERSON_TOKENS = {
    # English
    "love",
    "life",
    "music",
    "coffee",
    "python",
    "django",
    "developer",
    "coding",
    "code",
    "fitness",
    "gym",
    "travel",
    "fashion",
    "art",
    "food",
    "nature",
    "photo",
    "photography",
    "football",
    "family",
    "work",
    "business",
    "tehran",
    "iran",
    # Persian
    "عشق",
    "زندگی",
    "موسیقی",
    "قهوه",
    "برنامه",
    "برنامه‌نویسی",
    "برنامه نویسی",
    "ورزش",
    "باشگاه",
    "سفر",
    "مد",
    "هنر",
    "غذا",
    "طبیعت",
    "عکاسی",
    "فوتبال",
    "خانواده",
    "کار",
    "تهران",
    "ایران",
}


def _contains_red_heart(
    text: str,
) -> bool:
    """Return whether text contains a red-heart variant."""

    return any(heart in text for heart in _RED_HEART_VARIANTS)


def _contains_generic_heart(
    text: str,
) -> bool:
    """Return whether text contains a generic romantic heart."""

    return any(heart in text for heart in _GENERIC_HEARTS)


def _contains_decorative_heart(
    text: str,
) -> bool:
    """Return whether text contains another heart-color variant."""

    return any(heart in text for heart in _DECORATIVE_HEARTS)


def _candidate_name_from_match(
    match: re.Match[str],
) -> str | None:
    """
    Extract the text token adjacent to an emoji.

    This remains heuristic. The caller must still reject known
    non-person semantic tokens.
    """

    matched = match.group(0)

    cleaned = matched

    for emoji in (
        _RING,
        *_RED_HEART_VARIANTS,
    ):
        cleaned = cleaned.replace(
            emoji,
            " ",
        )

    cleaned = normalize_text(
        cleaned,
    ).strip()

    return cleaned or None


def _is_plausible_name(
    value: str | None,
) -> bool:
    """
    Return whether one adjacent token is plausible as a person's name.

    This intentionally performs only conservative lexical filtering.
    It does not claim that the token is actually a real person's name.
    """

    if value is None:
        return False

    normalized = normalize_text(
        value,
    )

    if not normalized:
        return False

    if normalized in _NON_PERSON_TOKENS:
        return False

    return len(normalized) >= 2


def _append_once(
    signals: list[RelationshipSignal],
    signal: RelationshipSignal,
) -> None:
    """Append a signal unless the same signal kind already exists."""

    if any(existing.kind is signal.kind for existing in signals):
        return

    signals.append(
        signal,
    )


@dataclass(frozen=True, slots=True)
class RelationshipSignalExtractor:
    """
    Extract contextual relationship-themed signals from public text.

    Signals are not relationship-status facts.

    Default weights represent semantic prior strength only.
    They are not calibrated probabilities and may later be replaced
    or adjusted by a learned/calibrated model.
    """

    ring_weight: float = 0.45

    red_heart_weight: float = 0.18

    generic_heart_weight: float = 0.10

    decorative_heart_weight: float = 0.05

    name_adjacent_ring_weight: float = 0.60

    name_adjacent_heart_weight: float = 0.30

    ring_and_heart_weight: float = 0.52

    def extract(
        self,
        text: str,
    ) -> tuple[RelationshipSignal, ...]:
        """Extract contextual relationship signals."""

        normalized = normalize_text(
            text,
            lowercase=False,
        )

        if not normalized:
            return ()

        signals: list[RelationshipSignal] = []

        self._extract_name_adjacent_ring(
            normalized,
            signals,
        )

        self._extract_name_adjacent_heart(
            normalized,
            signals,
        )

        has_ring = _RING in normalized

        has_red_heart = _contains_red_heart(
            normalized,
        )

        if has_ring and has_red_heart:
            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.RING_EMOJI,
                    raw_value="💍+❤️",
                    weight=self.ring_and_heart_weight,
                    context=normalized,
                ),
            )

        elif has_ring and not any(
            item.kind is RelationshipSignalKind.NAME_ADJACENT_RING for item in signals
        ):
            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.RING_EMOJI,
                    raw_value=_RING,
                    weight=self.ring_weight,
                    context=normalized,
                ),
            )

        if has_red_heart and not any(
            item.kind is RelationshipSignalKind.NAME_ADJACENT_HEART for item in signals
        ):
            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.RED_HEART_EMOJI,
                    raw_value="❤️",
                    weight=self.red_heart_weight,
                    context=normalized,
                ),
            )

        if _contains_generic_heart(
            normalized,
        ):
            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.HEART_EMOJI,
                    raw_value="generic_heart",
                    weight=self.generic_heart_weight,
                    context=normalized,
                ),
            )

        if _contains_decorative_heart(
            normalized,
        ):
            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.HEART_EMOJI,
                    raw_value="decorative_heart",
                    weight=self.decorative_heart_weight,
                    context=normalized,
                ),
            )

        return tuple(signals)

    def _extract_name_adjacent_ring(
        self,
        text: str,
        signals: list[RelationshipSignal],
    ) -> None:
        """Extract ring signals adjacent to plausible names."""

        for match in _NAME_RING_PATTERN.finditer(
            text,
        ):
            candidate = _candidate_name_from_match(
                match,
            )

            if not _is_plausible_name(
                candidate,
            ):
                continue

            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.NAME_ADJACENT_RING,
                    raw_value=match.group(0),
                    weight=self.name_adjacent_ring_weight,
                    context=text,
                ),
            )

            return

    def _extract_name_adjacent_heart(
        self,
        text: str,
        signals: list[RelationshipSignal],
    ) -> None:
        """Extract red-heart signals adjacent to plausible names."""

        for match in _NAME_RED_HEART_PATTERN.finditer(
            text,
        ):
            candidate = _candidate_name_from_match(
                match,
            )

            if not _is_plausible_name(
                candidate,
            ):
                continue

            _append_once(
                signals,
                RelationshipSignal(
                    kind=RelationshipSignalKind.NAME_ADJACENT_HEART,
                    raw_value=match.group(0),
                    weight=self.name_adjacent_heart_weight,
                    context=text,
                ),
            )

            return
