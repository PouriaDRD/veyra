"""Confidence calculation utilities."""

from collections.abc import Iterable

from .entities import Evidence


def combine_confidences(
    evidence: Iterable[Evidence],
) -> float:
    """
    Combine independent supporting confidence values.

    Uses the probabilistic union formula:

        1 - Π(1 - confidence)

    Multiple independent pieces of supporting evidence therefore increase
    confidence without exceeding 1.0.
    """

    items = tuple(evidence)

    if not items:
        return 0.0

    remaining_uncertainty = 1.0

    for item in items:
        remaining_uncertainty *= 1.0 - item.confidence

    return round(
        1.0 - remaining_uncertainty,
        6,
    )


def conflict_confidence(
    evidence: Iterable[Evidence],
) -> float:
    """
    Return confidence that evidence is genuinely conflicted.

    Conflict strength is based on the two strongest contradictory pieces
    of evidence and is intentionally conservative.
    """

    confidences = sorted(
        (item.confidence for item in evidence),
        reverse=True,
    )

    if len(confidences) < 2:
        return 0.0

    return round(
        min(
            confidences[0],
            confidences[1],
        ),
        6,
    )
