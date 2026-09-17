"""Relationship hypothesis adapter and strategy."""

from collections.abc import Iterable
from dataclasses import dataclass

from veyra.domain.evidence.entities import (
    Evidence,
    Fact,
)
from veyra.domain.evidence.enums import (
    FactKind,
    FactStatus,
)
from veyra.domain.evidence.resolver import (
    FactResolver,
)

from .enums import (
    HypothesisKind,
    RelationshipSignalKind,
    RelationshipStatus,
)
from .hypotheses import (
    HypothesisDefinition,
    HypothesisObservation,
    ObservationPolarity,
)
from .relationship import RelationshipSignal
from .strategies import StaticHypothesisStrategy

_RELATIONSHIP_VALUES = {status.value for status in RelationshipStatus}


RELATIONSHIP_HYPOTHESIS_DEFINITION = HypothesisDefinition(
    kind=HypothesisKind.RELATIONSHIP_STATUS,
    allowed_values=(
        RelationshipStatus.SINGLE.value,
        RelationshipStatus.MARRIED.value,
        RelationshipStatus.ENGAGED.value,
        RelationshipStatus.IN_RELATIONSHIP.value,
        RelationshipStatus.DIVORCED.value,
        RelationshipStatus.WIDOWED.value,
        RelationshipStatus.UNKNOWN.value,
    ),
    unknown_value=RelationshipStatus.UNKNOWN.value,
)


RELATIONSHIP_HYPOTHESIS_STRATEGY = StaticHypothesisStrategy(
    definition=RELATIONSHIP_HYPOTHESIS_DEFINITION,
)


@dataclass(frozen=True, slots=True)
class RelationshipHypothesisAdapter:
    """
    Convert relationship facts and contextual signals into generic observations.

    Explicit relationship facts receive stronger semantic influence than
    contextual emoji/name signals.

    Contextual signals do not establish an exact relationship status.
    """

    explicit_fact_weight: float = 1.0

    ring_support_weight: float = 0.45

    name_ring_support_weight: float = 0.60

    red_heart_support_weight: float = 0.18

    name_heart_support_weight: float = 0.30

    generic_heart_support_weight: float = 0.10

    def from_fact(
        self,
        fact: Fact | None,
    ) -> tuple[HypothesisObservation, ...]:
        """
        Convert relationship fact state into generic observations.

        Explicit supported facts become strong conflict-capable observations.

        Conflicted facts preserve every competing explicit interpretation.
        """

        if fact is None:
            return ()

        if fact.kind is not FactKind.RELATIONSHIP_STATUS:
            return ()

        if fact.status is FactStatus.UNKNOWN:
            return ()

        if fact.status is FactStatus.CONFLICTED:
            return self._from_conflicted_fact(
                fact,
            )

        if fact.status is not FactStatus.SUPPORTED:
            return ()

        value = fact.value

        if not isinstance(
            value,
            str,
        ):
            return ()

        if value not in _RELATIONSHIP_VALUES:
            return ()

        return (
            HypothesisObservation(
                target_value=value,
                polarity=ObservationPolarity.SUPPORT,
                weight=self.explicit_fact_weight,
                confidence=fact.confidence,
                source="relationship_fact",
                explanation=("Explicit public relationship-status claim."),
                correlation_key=(f"fact:{fact.id}"),
                conflict_eligible=True,
            ),
        )

    def from_signals(
        self,
        signals: Iterable[RelationshipSignal],
    ) -> tuple[HypothesisObservation, ...]:
        """
        Convert contextual relationship signals into generic observations.

        Emoji/name signals conservatively support broad relationship-present
        candidates.

        They do not establish marriage, engagement, or another exact status.

        Multiple candidate observations produced from one signal share the same
        correlation key so one signal cannot artificially inflate confidence.
        """

        observations: list[HypothesisObservation] = []

        for signal in signals:
            observations.extend(
                self._observations_for_signal(
                    signal,
                )
            )

        return tuple(
            observations,
        )

    def combine(
        self,
        *,
        fact: Fact | None = None,
        signals: Iterable[RelationshipSignal] = (),
    ) -> tuple[HypothesisObservation, ...]:
        """
        Combine explicit facts and contextual signals.

        Fact and signal inputs stay semantically distinct until they are
        normalized into generic hypothesis observations.
        """

        return (
            *self.from_fact(
                fact,
            ),
            *self.from_signals(
                signals,
            ),
        )

    def _from_conflicted_fact(
        self,
        fact: Fact,
    ) -> tuple[HypothesisObservation, ...]:
        """
        Preserve competing explicit relationship interpretations.

        Each distinct explicit evidence interpretation remains conflict-capable
        because these represent actual competing factual claims.
        """

        observations: list[HypothesisObservation] = []

        seen: set[str] = set()

        for evidence in fact.evidence:
            value = evidence.normalized_value

            if not isinstance(
                value,
                str,
            ):
                continue

            if value not in _RELATIONSHIP_VALUES:
                continue

            if value in seen:
                continue

            seen.add(
                value,
            )

            observations.append(
                HypothesisObservation(
                    target_value=value,
                    polarity=ObservationPolarity.SUPPORT,
                    weight=self.explicit_fact_weight,
                    confidence=evidence.confidence,
                    source="relationship_fact_conflict",
                    explanation=("Competing explicit public relationship-status claim."),
                    correlation_key=(f"evidence:{evidence.id}"),
                    conflict_eligible=True,
                )
            )

        return tuple(
            observations,
        )

    def _observations_for_signal(
        self,
        signal: RelationshipSignal,
    ) -> tuple[HypothesisObservation, ...]:
        """
        Map one contextual relationship signal into generic observations.

        Broad contextual signals fan out across several non-single candidates,
        but all observations created from one source share a correlation key.

        They are also marked ``conflict_eligible=False`` because ambiguity is
        not the same thing as contradictory evidence.
        """

        correlation_key = (
            f"relationship-signal:{signal.kind.value}:{signal.raw_value}:{signal.context or ''}"
        )

        if signal.kind is RelationshipSignalKind.NAME_ADJACENT_RING:
            return self._support_non_single_candidates(
                weight=min(
                    signal.weight,
                    self.name_ring_support_weight,
                ),
                source="name_adjacent_ring",
                explanation=("A ring emoji appears adjacent to a plausible name."),
                correlation_key=correlation_key,
            )

        if signal.kind is RelationshipSignalKind.RING_EMOJI:
            return self._support_non_single_candidates(
                weight=min(
                    signal.weight,
                    self.ring_support_weight,
                ),
                source="ring_emoji",
                explanation=("A ring emoji appears in public profile text."),
                correlation_key=correlation_key,
            )

        if signal.kind is RelationshipSignalKind.NAME_ADJACENT_HEART:
            return self._support_non_single_candidates(
                weight=min(
                    signal.weight,
                    self.name_heart_support_weight,
                ),
                source="name_adjacent_heart",
                explanation=("A red heart appears adjacent to a plausible name."),
                correlation_key=correlation_key,
            )

        if signal.kind is RelationshipSignalKind.RED_HEART_EMOJI:
            return self._support_non_single_candidates(
                weight=min(
                    signal.weight,
                    self.red_heart_support_weight,
                ),
                source="red_heart_emoji",
                explanation=("A red heart appears in public profile text."),
                correlation_key=correlation_key,
            )

        if signal.kind is RelationshipSignalKind.HEART_EMOJI:
            return self._support_non_single_candidates(
                weight=min(
                    signal.weight,
                    self.generic_heart_support_weight,
                ),
                source="heart_emoji",
                explanation=("A relationship-themed heart emoji appears in public profile text."),
                correlation_key=correlation_key,
            )

        return ()

    @staticmethod
    def _support_non_single_candidates(
        *,
        weight: float,
        source: str,
        explanation: str,
        correlation_key: str,
    ) -> tuple[HypothesisObservation, ...]:
        """
        Conservatively support relationship-present candidates.

        Contextual signals do not reliably distinguish between:
        - married
        - engaged
        - in relationship

        Therefore one contextual signal supports all three candidates.

        All observations share one correlation key because they originate from
        the same underlying signal.

        They are not conflict-capable because this is ambiguity, not evidence
        of contradictory factual claims.
        """

        if weight <= 0:
            return ()

        return tuple(
            HypothesisObservation(
                target_value=status.value,
                polarity=ObservationPolarity.SUPPORT,
                weight=weight,
                confidence=1.0,
                source=source,
                explanation=explanation,
                correlation_key=correlation_key,
                conflict_eligible=False,
            )
            for status in (
                RelationshipStatus.MARRIED,
                RelationshipStatus.ENGAGED,
                RelationshipStatus.IN_RELATIONSHIP,
            )
        )


def build_relationship_fact(
    evidence: Iterable[Evidence],
) -> Fact:
    """
    Resolve explicit relationship evidence through the generic fact resolver.

    Relationship facts intentionally use the same confidence and conflict
    semantics as every other Veyra fact.
    """

    return FactResolver().resolve(
        FactKind.RELATIONSHIP_STATUS,
        evidence,
    )
