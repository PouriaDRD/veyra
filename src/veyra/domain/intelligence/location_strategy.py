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
    Convert location facts and signals into generic observations.

    Exact explicit CITY facts receive the strongest influence.

    Contextual and observed sources contribute according to their semantic
    reliability without automatically becoming facts.
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
        """
        Convert a resolved CITY fact into hypothesis observations.

        COUNTRY facts are intentionally ignored here because LIKELY_LOCATION
        currently resolves city-level candidates.
        """

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
                explanation=("Explicit public city claim."),
                correlation_key=(f"fact:{fact.id}"),
                conflict_eligible=True,
            ),
        )

    def from_signals(
        self,
        signals: Iterable[LocationSignal],
    ) -> tuple[HypothesisObservation, ...]:
        """Convert normalized location signals into observations."""

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
        """Combine explicit city facts and contextual location signals."""

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
        """Preserve competing explicit city interpretations."""

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
                    explanation=("Competing explicit public city claim."),
                    correlation_key=(f"evidence:{evidence.id}"),
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
        """Convert one location signal into a generic observation."""

        weight = self._weight_for_signal(
            signal,
        )

        if weight <= 0:
            return None

        source = f"location_signal:{signal.kind.value}"

        return HypothesisObservation(
            target_value=signal.value,
            polarity=ObservationPolarity.SUPPORT,
            weight=weight,
            confidence=signal.confidence,
            source=source,
            explanation=self._explanation_for_signal(
                signal,
            ),
            correlation_key=(f"location-signal:{signal.id}"),
            conflict_eligible=False,
        )

    def _weight_for_signal(
        self,
        signal: LocationSignal,
    ) -> float:
        """
        Return bounded semantic weight for one signal.

        The signal's own weight may lower but never exceed the adapter's
        source-specific maximum.
        """

        maximum = {
            LocationSignalKind.PROFILE_METADATA: (self.profile_metadata_weight),
            LocationSignalKind.GEOTAG: (self.geotag_weight),
            LocationSignalKind.BIO_MENTION: (self.bio_mention_weight),
            LocationSignalKind.CAPTION_MENTION: (self.caption_mention_weight),
        }[signal.kind]

        return min(
            signal.weight,
            maximum,
        )

    @staticmethod
    def _explanation_for_signal(
        signal: LocationSignal,
    ) -> str:
        """Return deterministic explanation text for one signal."""

        if signal.kind is LocationSignalKind.PROFILE_METADATA:
            return f"Public profile metadata indicates the location '{signal.value}'."

        if signal.kind is LocationSignalKind.GEOTAG:
            return f"A public geotag indicates the location '{signal.value}'."

        if signal.kind is LocationSignalKind.BIO_MENTION:
            return f"Public biography text mentions the location '{signal.value}'."

        return f"Public content mentions the location '{signal.value}'."
