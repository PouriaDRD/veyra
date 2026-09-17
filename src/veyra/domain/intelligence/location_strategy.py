"""Location hypothesis adapter and strategy."""

from collections.abc import Iterable
from dataclasses import dataclass

from veyra.domain.evidence.entities import Fact
from veyra.domain.evidence.enums import (
    FactKind,
    FactStatus,
)

from .enums import (
    HypothesisKind,
    LocationRelation,
    LocationSignalKind,
)
from .hypotheses import (
    HypothesisDefinition,
    HypothesisObservation,
    ObservationPolarity,
)
from .location_signals import LocationSignal
from .strategies import StaticHypothesisStrategy

LIKELY_LOCATION_HYPOTHESIS_DEFINITION = HypothesisDefinition(
    kind=HypothesisKind.LIKELY_LOCATION,
    allowed_values=("unknown",),
    unknown_value="unknown",
    allow_observed_values=True,
)

LIKELY_LOCATION_HYPOTHESIS_STRATEGY = StaticHypothesisStrategy(
    definition=LIKELY_LOCATION_HYPOTHESIS_DEFINITION,
)


@dataclass(frozen=True, slots=True)
class LocationHypothesisAdapter:
    """
    Convert current-location facts and compatible signals into observations.

    ``LIKELY_LOCATION`` currently means likely current location.

    Origin/hometown evidence is therefore preserved as a signal but is not
    allowed to support this hypothesis.
    """

    explicit_city_fact_weight: float = 1.0

    profile_metadata_weight: float = 0.90
    geotag_weight: float = 0.75
    bio_mention_weight: float = 0.35
    caption_mention_weight: float = 0.25

    def from_fact(
        self,
        fact: Fact | None,
    ) -> tuple[HypothesisObservation, ...]:
        """Convert a resolved current CITY fact into observations."""

        if fact is None:
            return ()

        if fact.kind is not FactKind.CITY:
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

        normalized = value.strip().casefold()

        if not normalized:
            return ()

        return (
            HypothesisObservation(
                target_value=normalized,
                polarity=ObservationPolarity.SUPPORT,
                weight=self.explicit_city_fact_weight,
                confidence=fact.confidence,
                source="city_fact",
                explanation="Explicit public current-city claim.",
                correlation_key=f"fact:{fact.id}",
                conflict_eligible=True,
            ),
        )

    def from_signals(
        self,
        signals: Iterable[LocationSignal],
    ) -> tuple[HypothesisObservation, ...]:
        """Convert compatible normalized location signals into observations."""

        observations: list[HypothesisObservation] = []

        for signal in signals:
            observation = self._observation_for_signal(
                signal,
            )

            if observation is not None:
                observations.append(
                    observation,
                )

        return tuple(
            observations,
        )

    def combine(
        self,
        *,
        city_fact: Fact | None = None,
        signals: Iterable[LocationSignal] = (),
    ) -> tuple[HypothesisObservation, ...]:
        """Combine current city facts and compatible location signals."""

        return (
            *self.from_fact(
                city_fact,
            ),
            *self.from_signals(
                signals,
            ),
        )

    def _from_conflicted_fact(
        self,
        fact: Fact,
    ) -> tuple[HypothesisObservation, ...]:
        """Preserve competing explicit current-city interpretations."""

        observations: list[HypothesisObservation] = []
        seen: set[str] = set()

        for evidence in fact.evidence:
            value = evidence.normalized_value

            if not isinstance(
                value,
                str,
            ):
                continue

            normalized = value.strip().casefold()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(
                normalized,
            )

            observations.append(
                HypothesisObservation(
                    target_value=normalized,
                    polarity=ObservationPolarity.SUPPORT,
                    weight=self.explicit_city_fact_weight,
                    confidence=evidence.confidence,
                    source="city_fact_conflict",
                    explanation="Competing explicit public current-city claim.",
                    correlation_key=f"evidence:{evidence.id}",
                    conflict_eligible=True,
                )
            )

        return tuple(
            observations,
        )

    def _observation_for_signal(
        self,
        signal: LocationSignal,
    ) -> HypothesisObservation | None:
        """Convert one compatible location signal into an observation."""

        if signal.relation is LocationRelation.ORIGIN:
            return None

        weight = self._weight_for_signal(
            signal,
        )

        if weight <= 0:
            return None

        return HypothesisObservation(
            target_value=signal.value,
            polarity=ObservationPolarity.SUPPORT,
            weight=weight,
            confidence=signal.confidence,
            source=f"location_signal:{signal.kind.value}",
            explanation=self._explanation_for_signal(
                signal,
            ),
            correlation_key=f"location-signal:{signal.id}",
            conflict_eligible=False,
        )

    def _weight_for_signal(
        self,
        signal: LocationSignal,
    ) -> float:
        """Return bounded semantic weight for one signal."""

        maximum = {
            LocationSignalKind.PROFILE_METADATA: self.profile_metadata_weight,
            LocationSignalKind.GEOTAG: self.geotag_weight,
            LocationSignalKind.BIO_MENTION: self.bio_mention_weight,
            LocationSignalKind.CAPTION_MENTION: self.caption_mention_weight,
        }[signal.kind]

        return min(
            signal.weight,
            maximum,
        )

    @staticmethod
    def _explanation_for_signal(
        signal: LocationSignal,
    ) -> str:
        """Return deterministic explanation text."""

        if signal.kind is LocationSignalKind.PROFILE_METADATA:
            return f"Public profile metadata indicates the location '{signal.value}'."

        if signal.kind is LocationSignalKind.GEOTAG:
            return f"A public geotag indicates the location '{signal.value}'."

        if signal.kind is LocationSignalKind.BIO_MENTION:
            return f"Public biography text contextually mentions the location '{signal.value}'."

        return f"Public content mentions the location '{signal.value}'."
