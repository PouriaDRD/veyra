"""Shared Unicode-safe location text matching utilities."""

import re

from .text import normalize_text

TextSpan = tuple[
    int,
    int,
]


def location_alias_pattern(
    alias: str,
) -> str:
    """
    Build a normalized Unicode-safe location alias pattern.

    ``(?<!\\w)`` and ``(?!\\w)`` prevent substring matches such as:

    - Tehran inside Tehrani
    - Iran inside Iranian

    Python's Unicode-aware ``\\w`` handling also works for Persian letters.
    """

    normalized = normalize_text(
        alias,
    )

    if not normalized:
        raise ValueError(
            "location alias must not be empty.",
        )

    escaped = re.escape(
        normalized,
    )

    flexible_whitespace = escaped.replace(
        r"\ ",
        r"\s+",
    )

    return rf"(?<!\w)" rf"{flexible_whitespace}" rf"(?!\w)"


def find_pattern_spans(
    text: str,
    pattern: str,
) -> tuple[TextSpan, ...]:
    """Return every match span for one case-insensitive pattern."""

    return tuple(
        match.span()
        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        )
    )


def spans_overlap(
    left: TextSpan,
    right: TextSpan,
) -> bool:
    """Return whether two half-open text spans overlap."""

    return left[0] < right[1] and right[0] < left[1]


def overlaps_any(
    span: TextSpan,
    others: tuple[TextSpan, ...],
) -> bool:
    """Return whether one span overlaps any span in a collection."""

    return any(
        spans_overlap(
            span,
            other,
        )
        for other in others
    )


def context_spans_for_alias(
    text: str,
    *,
    alias: str,
    context_patterns: tuple[str, ...],
) -> tuple[TextSpan, ...]:
    """
    Return context spans involving one normalized location alias.

    Each context pattern must contain a ``{alias}`` placeholder.
    """

    alias_pattern = location_alias_pattern(
        alias,
    )

    spans: list[TextSpan] = []

    for template in context_patterns:
        pattern = template.format(
            alias=alias_pattern,
        )

        spans.extend(
            find_pattern_spans(
                text,
                pattern,
            )
        )

    return tuple(
        spans,
    )
