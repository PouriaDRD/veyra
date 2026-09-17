"""Evidence-to-fact resolution engine."""

from collections import defaultdict
from collections.abc import Iterable

from .cardinality import fact_cardinality_for
from .confidence import (
    combine_confidences,
    conflict_confidence,
)
from .entities import Evidence, Fact, FactValue
from .enums import FactCardinality, FactKind, FactStatus


class FactResolver:
    """
    Resolve raw evidence into one normalized fact.

    Definitive evidence controls contradiction detection.

    Ambiguous evidence represents alternative interpretations of one raw
    observation. It may strengthen a definitive interpretation when values
    agree, but an unmatched ambiguous hypothesis does not create a hard
    contradiction against otherwise consistent definitive evidence.

    Multi-value fact kinds allow several definitive normalized values to remain
    simultaneously supported rather than treating them as contradictions.
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

        definitive_items = tuple(item for item in items if not item.is_ambiguous)

        if definitive_items:
            if fact_cardinality_for(kind) is FactCardinality.MULTIPLE:
                return self._resolve_multiple_with_definitive_evidence(
                    kind=kind,
                    all_items=items,
                    definitive_items=definitive_items,
                )

            return self._resolve_single_with_definitive_evidence(
                kind=kind,
                all_items=items,
                definitive_items=definitive_items,
            )

        return self._resolve_ambiguous_only(
            kind=kind,
            items=items,
        )

    @staticmethod
    def _resolve_single_with_definitive_evidence(
        *,
        kind: FactKind,
        all_items: tuple[Evidence, ...],
        definitive_items: tuple[Evidence, ...],
    ) -> Fact:
        """Resolve scalar evidence when at least one definitive claim exists."""

        grouped_definitive: dict[
            FactValue,
            list[Evidence],
        ] = defaultdict(list)

        for item in definitive_items:
            grouped_definitive[item.normalized_value].append(
                item,
            )

        if len(grouped_definitive) > 1:
            return Fact(
                kind=kind,
                status=FactStatus.CONFLICTED,
                confidence=conflict_confidence(
                    definitive_items,
                ),
                evidence=all_items,
            )

        resolved_value = next(iter(grouped_definitive))

        supporting_items = tuple(
            item for item in all_items if item.normalized_value == resolved_value
        )

        return Fact(
            kind=kind,
            status=FactStatus.SUPPORTED,
            value=resolved_value,
            confidence=combine_confidences(
                supporting_items,
            ),
            evidence=supporting_items,
        )

    @staticmethod
    def _resolve_multiple_with_definitive_evidence(
        *,
        kind: FactKind,
        all_items: tuple[Evidence, ...],
        definitive_items: tuple[Evidence, ...],
    ) -> Fact:
        """
        Resolve a multi-value fact from definitive public claims.

        Distinct definitive values are compatible. Ambiguous evidence may
        strengthen a definitive value when it matches that value; unmatched
        ambiguous alternatives do not become independently supported values.
        """

        grouped_definitive: dict[
            FactValue,
            list[Evidence],
        ] = defaultdict(list)

        for item in definitive_items:
            grouped_definitive[item.normalized_value].append(
                item,
            )

        resolved_values = tuple(
            sorted(
                grouped_definitive.keys(),
                key=str,
            )
        )

        supporting_items = tuple(
            item for item in all_items if item.normalized_value in grouped_definitive
        )

        value_confidences = tuple(
            combine_confidences(
                tuple(item for item in supporting_items if item.normalized_value == value)
            )
            for value in resolved_values
        )

        return Fact(
            kind=kind,
            status=FactStatus.SUPPORTED,
            values=resolved_values,
            confidence=min(
                value_confidences,
            ),
            evidence=supporting_items,
        )

    @staticmethod
    def _resolve_ambiguous_only(
        *,
        kind: FactKind,
        items: tuple[Evidence, ...],
    ) -> Fact:
        """Resolve a collection containing only ambiguous hypotheses."""

        grouped: dict[
            FactValue,
            list[Evidence],
        ] = defaultdict(list)

        for item in items:
            grouped[item.normalized_value].append(
                item,
            )

        if len(grouped) == 1:
            value, matching_items = next(iter(grouped.items()))

            if fact_cardinality_for(kind) is FactCardinality.MULTIPLE:
                return Fact(
                    kind=kind,
                    status=FactStatus.SUPPORTED,
                    values=(value,),
                    confidence=combine_confidences(
                        matching_items,
                    ),
                    evidence=tuple(
                        matching_items,
                    ),
                )

            return Fact(
                kind=kind,
                status=FactStatus.SUPPORTED,
                value=value,
                confidence=combine_confidences(
                    matching_items,
                ),
                evidence=tuple(
                    matching_items,
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
