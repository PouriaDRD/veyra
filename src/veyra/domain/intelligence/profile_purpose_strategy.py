"""Profile-purpose hypothesis adapter and strategy."""

from collections.abc import Iterable
from dataclasses import dataclass

from .enums import (
    HypothesisKind,
    ProfilePurpose,
)
from .hypotheses import (
    HypothesisDefinition,
    HypothesisObservation,
    ObservationPolarity,
)
from .profile_purpose import ProfilePurposeSignal
from .strategies import StaticHypothesisStrategy

PROFILE_PURPOSE_HYPOTHESIS_DEFINITION = HypothesisDefinition(
    kind=HypothesisKind.PROFILE_PURPOSE,
    allowed_values=tuple(purpose.value for purpose in ProfilePurpose),
    unknown_value=ProfilePurpose.UNKNOWN.value,
)


PROFILE_PURPOSE_HYPOTHESIS_STRATEGY = StaticHypothesisStrategy(
    definition=PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
)


@dataclass(frozen=True, slots=True)
class ProfilePurposeHypothesisAdapter:
    """
    Convert profile-purpose signals into generic hypothesis observations.

    ``source`` identifies which public profile field produced the signals.

    ``correlation_key`` should be shared by signals derived from the same
    underlying field observation. This prevents one biography or display-name
    field containing several semantic markers from artificially inflating
    overall hypothesis confidence.

    Candidate scores remain domain-neutral and are still calculated by the
    generic hypothesis engine.
    """

    def from_signals(
        self,
        signals: Iterable[ProfilePurposeSignal],
        *,
        source: str = "profile_text",
        correlation_key: str | None = None,
    ) -> tuple[HypothesisObservation, ...]:
        """Convert normalized profile-purpose signals into observations."""

        normalized_source = source.strip()

        if not normalized_source:
            raise ValueError(
                "profile-purpose observation source must not be empty.",
            )

        normalized_correlation_key = correlation_key

        if normalized_correlation_key is not None:
            normalized_correlation_key = normalized_correlation_key.strip() or None

        observations: list[HypothesisObservation] = []

        for signal in signals:
            signal_correlation_key = (
                normalized_correlation_key
                if normalized_correlation_key is not None
                else (f"profile-purpose-signal:{signal.id}")
            )

            observations.append(
                HypothesisObservation(
                    target_value=signal.purpose.value,
                    polarity=ObservationPolarity.SUPPORT,
                    weight=signal.weight,
                    confidence=signal.confidence,
                    source=(f"profile_purpose_signal:{normalized_source}:{signal.kind.value}"),
                    explanation=self._explanation_for_signal(
                        signal,
                        source=normalized_source,
                    ),
                    correlation_key=signal_correlation_key,
                    conflict_eligible=False,
                )
            )

        return tuple(
            observations,
        )

    @staticmethod
    def _explanation_for_signal(
        signal: ProfilePurposeSignal,
        *,
        source: str,
    ) -> str:
        """Return deterministic explanation text."""

        return (
            f"Public profile {source} contains a "
            f"'{signal.kind.value}' marker supporting "
            f"'{signal.purpose.value}'."
        )
