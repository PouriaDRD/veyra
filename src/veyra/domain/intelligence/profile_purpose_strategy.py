"""Profile-purpose hypothesis adapter and strategy."""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

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

PROFILE_PURPOSE_HYPOTHESIS_DEFINITION = HypothesisDefinition(
    kind=HypothesisKind.PROFILE_PURPOSE,
    allowed_values=tuple(purpose.value for purpose in ProfilePurpose),
    unknown_value=ProfilePurpose.UNKNOWN.value,
)


_MIXED_ELIGIBLE_PURPOSES = frozenset(
    {
        ProfilePurpose.PROFESSIONAL.value,
        ProfilePurpose.CREATOR.value,
        ProfilePurpose.BUSINESS.value,
        ProfilePurpose.ORGANIZATION.value,
    }
)


def _observation_correlation_key(
    observation: HypothesisObservation,
) -> str:
    """
    Return the effective correlation identity for one observation.

    The generic engine treats observations without an explicit correlation key
    as independent. We mirror the same behavior here while preparing
    profile-purpose observations.
    """

    if observation.correlation_key is not None:
        return observation.correlation_key

    return f"observation:{observation.id}"


def _pair_strength(
    first: HypothesisObservation,
    second: HypothesisObservation,
) -> float:
    """
    Combine two independent strengths using bounded-union mathematics.

    This matches the generic engine's support-combination semantics.

    The value is a deterministic model score, not a calibrated probability.
    """

    return round(
        1.0 - ((1.0 - first.effective_strength) * (1.0 - second.effective_strength)),
        6,
    )


def _observation_sort_key(
    observation: HypothesisObservation,
) -> tuple[
    str,
    str,
    float,
    str,
    str,
]:
    """Return a stable semantic ordering key."""

    return (
        _observation_correlation_key(
            observation,
        ),
        observation.target_value,
        -observation.effective_strength,
        observation.source,
        observation.explanation,
    )


@dataclass(frozen=True, slots=True)
class ProfilePurposeHypothesisStrategy:
    """
    Profile-purpose strategy with derived MIXED semantics.

    ``MIXED`` is never extracted directly from raw profile text.

    Instead it is derived when two sufficiently strong, independent,
    non-personal purpose observations support different profile purposes.

    Examples:

    Independent:
        display name -> CREATOR
        bio -> BUSINESS
        => MIXED

    Correlated:
        one bio -> CREATOR + BUSINESS
        => remains ordinary multi-candidate ambiguity

    Personal markers do not participate in MIXED derivation.
    """

    definition: HypothesisDefinition = PROFILE_PURPOSE_HYPOTHESIS_DEFINITION

    mixed_min_effective_strength: float = 0.50

    def __post_init__(self) -> None:
        """Validate strategy configuration."""

        if self.definition.kind is not HypothesisKind.PROFILE_PURPOSE:
            raise ValueError(
                "profile-purpose strategy requires PROFILE_PURPOSE definition.",
            )

        if not 0 <= self.mixed_min_effective_strength <= 1:
            raise ValueError(
                "mixed_min_effective_strength must be between 0 and 1.",
            )

    @property
    def kind(self) -> HypothesisKind:
        """Return the hypothesis kind handled by this strategy."""

        return self.definition.kind

    def prepare_observations(
        self,
        observations: Iterable[HypothesisObservation],
    ) -> tuple[HypothesisObservation, ...]:
        """
        Prepare observations and derive MIXED when warranted.

        The strongest valid independent pair is transformed into MIXED support.

        The original two observations are replaced rather than duplicated.
        This preserves their original weight, confidence, source, and
        correlation groups without artificially increasing inference
        confidence.
        """

        items = tuple(
            observations,
        )

        pair = self._select_mixed_pair(
            items,
        )

        if pair is None:
            return items

        first, second = pair

        prepared = [
            observation
            for observation in items
            if (observation is not first and observation is not second)
        ]

        prepared.extend(
            (
                self._as_mixed_observation(
                    first,
                ),
                self._as_mixed_observation(
                    second,
                ),
            )
        )

        return tuple(
            prepared,
        )

    def _select_mixed_pair(
        self,
        observations: tuple[
            HypothesisObservation,
            ...,
        ],
    ) -> (
        tuple[
            HypothesisObservation,
            HypothesisObservation,
        ]
        | None
    ):
        """
        Select the strongest valid independent purpose pair.

        A valid pair:
        - contains two SUPPORT observations
        - targets two different MIXED-eligible purposes
        - has sufficient effective strength
        - comes from two different correlation groups
        """

        eligible = tuple(
            sorted(
                (
                    observation
                    for observation in observations
                    if self._is_mixed_eligible(
                        observation,
                    )
                ),
                key=_observation_sort_key,
            )
        )

        valid_pairs: list[
            tuple[
                HypothesisObservation,
                HypothesisObservation,
            ]
        ] = []

        for first, second in combinations(
            eligible,
            2,
        ):
            if first.target_value == second.target_value:
                continue

            if _observation_correlation_key(
                first,
            ) == _observation_correlation_key(
                second,
            ):
                continue

            valid_pairs.append(
                (
                    first,
                    second,
                )
            )

        if not valid_pairs:
            return None

        return max(
            valid_pairs,
            key=self._mixed_pair_rank,
        )

    def _is_mixed_eligible(
        self,
        observation: HypothesisObservation,
    ) -> bool:
        """Return whether one observation may participate in MIXED."""

        if observation.polarity is not ObservationPolarity.SUPPORT:
            return False

        if observation.target_value not in _MIXED_ELIGIBLE_PURPOSES:
            return False

        return observation.effective_strength >= self.mixed_min_effective_strength

    @staticmethod
    def _mixed_pair_rank(
        pair: tuple[
            HypothesisObservation,
            HypothesisObservation,
        ],
    ) -> tuple[
        float,
        float,
        float,
        tuple[str, str],
        tuple[str, str],
    ]:
        """
        Rank valid MIXED pairs deterministically.

        Highest bounded combined support wins.

        Remaining fields provide stable semantic tie-breaking independent from
        incoming observation ordering.
        """

        first, second = pair

        strengths = sorted(
            (
                first.effective_strength,
                second.effective_strength,
            ),
            reverse=True,
        )

        targets = (
            min(
                first.target_value,
                second.target_value,
            ),
            max(
                first.target_value,
                second.target_value,
            ),
        )

        sources = (
            min(
                first.source,
                second.source,
            ),
            max(
                first.source,
                second.source,
            ),
        )

        return (
            _pair_strength(
                first,
                second,
            ),
            strengths[0],
            strengths[1],
            targets,
            sources,
        )

    @staticmethod
    def _as_mixed_observation(
        observation: HypothesisObservation,
    ) -> HypothesisObservation:
        """
        Retarget one underlying purpose observation toward MIXED.

        The same source, correlation identity, weight, and confidence are
        retained so the generic engine still sees the original independent
        evidence structure.
        """

        return HypothesisObservation(
            target_value=ProfilePurpose.MIXED.value,
            polarity=ObservationPolarity.SUPPORT,
            weight=observation.weight,
            confidence=observation.confidence,
            source=observation.source,
            explanation=(
                "Independent profile-purpose evidence originally supporting "
                f"'{observation.target_value}' contributes to a mixed "
                "profile-purpose classification."
            ),
            correlation_key=observation.correlation_key,
            conflict_eligible=False,
        )


PROFILE_PURPOSE_HYPOTHESIS_STRATEGY = ProfilePurposeHypothesisStrategy()


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
