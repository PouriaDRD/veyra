"""Evidence-to-fact resolution engine."""

from collections import defaultdict
from collections.abc import Iterable

from .confidence import (
    combine_confidences,
    conflict_confidence,
)
from .entities import Evidence, Fact, FactValue
from .enums import FactKind, FactStatus


class FactResolver:
    """
    Resolve raw evidence into one normalized fact.

    Evidence with identical normalized values supports the same fact.
    Multiple incompatible normalized values produce a conflicted fact.
    """

    def resolve(
        self,
        kind: FactKind,
        evidence: Iterable[Evidence],
    ) -> Fact:
        """Resolve evidence for one fact kind."""

        items = tuple(evidence)

        if not items:
            return Fact(
                kind=kind,
                status=FactStatus.UNKNOWN,
                confidence=0.0,
            )

        grouped: dict[
            FactValue,
            list[Evidence],
        ] = defaultdict(list)

        for item in items:
            grouped[item.normalized_value].append(
                item,
            )

        if len(grouped) == 1:
            value, matching_evidence = next(iter(grouped.items()))

            return Fact(
                kind=kind,
                status=FactStatus.SUPPORTED,
                value=value,
                confidence=combine_confidences(
                    matching_evidence,
                ),
                evidence=tuple(
                    matching_evidence,
                ),
            )

        return Fact(
            kind=kind,
            status=FactStatus.CONFLICTED,
            confidence=conflict_confidence(
                items,
            ),
            evidence=items,
        )
