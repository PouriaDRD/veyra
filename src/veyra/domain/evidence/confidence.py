"""Confidence calculation utilities."""

from collections import defaultdict
from collections.abc import Iterable

from .entities import Evidence, FactValue


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
    Measure the strength of a genuine cross-value conflict.

    Evidence is first grouped by normalized value.

    Matching evidence strengthens the interpretation it supports.
    Conflict confidence is then defined by the second-strongest competing
    interpretation, because a conflict can only be as strong as the weaker
    side of the two strongest incompatible interpretations.

    Evidence that supports only one normalized value is not conflicted.
    """

    grouped: dict[
        FactValue,
        list[Evidence],
    ] = defaultdict(list)

    for item in evidence:
        grouped[item.normalized_value].append(
            item,
        )

    if len(grouped) < 2:
        return 0.0

    interpretation_confidences = sorted(
        (
            combine_confidences(
                matching_evidence,
            )
            for matching_evidence in grouped.values()
        ),
        reverse=True,
    )

    return round(
        interpretation_confidences[1],
        6,
    )
