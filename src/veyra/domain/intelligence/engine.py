"""Generic explainable hypothesis inference engine."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .enums import HypothesisStatus
from .hypotheses import (
    HypothesisCandidateResult,
    HypothesisDefinition,
    HypothesisObservation,
    HypothesisResult,
    ObservationPolarity,
)


def _combine_strengths(
    strengths: Iterable[float],
) -> float:
    """
    Combine independent strengths using bounded union mathematics.

    The result is a deterministic model score, not a calibrated probability.
    """

    remaining = 1.0

    for strength in strengths:
        remaining *= 1.0 - strength

    return round(
        1.0 - remaining,
        6,
    )


@dataclass(frozen=True, slots=True)
class HypothesisEnginePolicy:
    """Generic thresholds used to classify inference strength."""

    possible_threshold: float = 0.20

    probable_threshold: float = 0.50

    strong_threshold: float = 0.75

    conflict_threshold: float = 0.45

    ambiguity_margin: float = 0.05

    algorithm_version: str = "hypothesis-v1"

    def __post_init__(self) -> None:
        """Validate engine policy."""

        thresholds = (
            self.possible_threshold,
            self.probable_threshold,
            self.strong_threshold,
            self.conflict_threshold,
            self.ambiguity_margin,
        )

        if any(not 0 <= threshold <= 1 for threshold in thresholds):
            raise ValueError(
                "hypothesis thresholds must be between 0 and 1.",
            )

        if not (self.possible_threshold <= self.probable_threshold <= self.strong_threshold):
            raise ValueError(
                "hypothesis thresholds must be ordered.",
            )

        algorithm_version = self.algorithm_version.strip()

        if not algorithm_version:
            raise ValueError(
                "algorithm_version must not be empty.",
            )

        object.__setattr__(
            self,
            "algorithm_version",
            algorithm_version,
        )


class HypothesisEngine:
    """
    Domain-agnostic explainable inference engine.

    Domain adapters convert facts/signals into generic observations before
    calling this engine.
    """

    def __init__(
        self,
        *,
        policy: HypothesisEnginePolicy | None = None,
    ) -> None:
        self._policy = policy if policy is not None else HypothesisEnginePolicy()

    def evaluate(
        self,
        definition: HypothesisDefinition,
        observations: Iterable[HypothesisObservation],
    ) -> HypothesisResult:
        """Evaluate observations against one hypothesis definition."""

        items = tuple(
            observations,
        )

        self._validate_observations(
            definition,
            items,
        )

        grouped_support: dict[
            str,
            list[HypothesisObservation],
        ] = defaultdict(list)

        grouped_opposition: dict[
            str,
            list[HypothesisObservation],
        ] = defaultdict(list)

        for observation in items:
            target = observation.target_value

            if observation.polarity is ObservationPolarity.SUPPORT:
                grouped_support[target].append(
                    observation,
                )

            else:
                grouped_opposition[target].append(
                    observation,
                )

        candidates = tuple(
            self._build_candidate(
                value=value,
                supporting=tuple(
                    grouped_support.get(
                        value,
                        (),
                    )
                ),
                opposing=tuple(
                    grouped_opposition.get(
                        value,
                        (),
                    )
                ),
            )
            for value in definition.allowed_values
        )

        if not items:
            return HypothesisResult(
                kind=definition.kind,
                status=HypothesisStatus.UNKNOWN,
                best_value=definition.unknown_value,
                confidence=0.0,
                candidates=candidates,
                algorithm_version=(self._policy.algorithm_version),
            )

        best_candidate = max(
            candidates,
            key=lambda candidate: candidate.score,
        )

        confidence = self._calculate_confidence(
            items,
        )

        status = self._resolve_status(
            candidates=candidates,
            best_candidate=best_candidate,
            unknown_value=definition.unknown_value,
        )

        best_value = best_candidate.value

        if status in {
            HypothesisStatus.UNKNOWN,
            HypothesisStatus.AMBIGUOUS,
        }:
            best_value = definition.unknown_value

        return HypothesisResult(
            kind=definition.kind,
            status=status,
            best_value=best_value,
            confidence=confidence,
            candidates=candidates,
            algorithm_version=(self._policy.algorithm_version),
        )

    @staticmethod
    def _validate_observations(
        definition: HypothesisDefinition,
        observations: tuple[
            HypothesisObservation,
            ...,
        ],
    ) -> None:
        """Reject observations targeting undefined candidate values."""

        allowed = set(
            definition.allowed_values,
        )

        invalid = {
            observation.target_value
            for observation in observations
            if observation.target_value not in allowed
        }

        if invalid:
            joined = ", ".join(
                sorted(
                    invalid,
                )
            )

            raise ValueError(
                f"observations contain unsupported target values: {joined}.",
            )

    @staticmethod
    def _build_candidate(
        *,
        value: str,
        supporting: tuple[
            HypothesisObservation,
            ...,
        ],
        opposing: tuple[
            HypothesisObservation,
            ...,
        ],
    ) -> HypothesisCandidateResult:
        """Build one candidate's support and opposition scores."""

        support = _combine_strengths(observation.effective_strength for observation in supporting)

        opposition = _combine_strengths(observation.effective_strength for observation in opposing)

        score = round(
            support * (1.0 - opposition),
            6,
        )

        return HypothesisCandidateResult(
            value=value,
            score=score,
            support=support,
            opposition=opposition,
            supporting_observations=supporting,
            opposing_observations=opposing,
        )

    @staticmethod
    def _calculate_confidence(
        observations: tuple[
            HypothesisObservation,
            ...,
        ],
    ) -> float:
        """
        Estimate confidence from independent underlying observations.

        Several candidate observations derived from one source share a
        ``correlation_key`` and therefore contribute only once.

        The strongest effective contribution from each correlated group is
        retained.
        """

        grouped: dict[
            str,
            list[float],
        ] = defaultdict(list)

        for observation in observations:
            key = (
                observation.correlation_key
                if observation.correlation_key is not None
                else f"observation:{observation.id}"
            )

            grouped[key].append(
                observation.effective_strength,
            )

        independent_strengths = (
            max(
                strengths,
            )
            for strengths in grouped.values()
        )

        return _combine_strengths(
            independent_strengths,
        )

    def _resolve_status(
        self,
        *,
        candidates: tuple[
            HypothesisCandidateResult,
            ...,
        ],
        best_candidate: HypothesisCandidateResult,
        unknown_value: str,
    ) -> HypothesisStatus:
        """Resolve qualitative hypothesis status."""

        non_unknown = tuple(
            candidate for candidate in candidates if candidate.value != unknown_value
        )

        ranked = sorted(
            non_unknown,
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        if not ranked:
            return HypothesisStatus.UNKNOWN

        strongest = ranked[0]

        if strongest.score < self._policy.possible_threshold:
            return HypothesisStatus.UNKNOWN

        if self._has_genuine_conflict(
            ranked,
        ):
            return HypothesisStatus.CONFLICTED

        second = ranked[1] if len(ranked) > 1 else None

        if (
            second is not None
            and second.score >= self._policy.possible_threshold
            and abs(strongest.score - second.score) <= self._policy.ambiguity_margin
        ):
            return HypothesisStatus.AMBIGUOUS

        if best_candidate.value == unknown_value:
            return HypothesisStatus.UNKNOWN

        if strongest.score >= self._policy.strong_threshold:
            return HypothesisStatus.STRONGLY_SUPPORTED

        if strongest.score >= self._policy.probable_threshold:
            return HypothesisStatus.PROBABLE

        return HypothesisStatus.POSSIBLE

    def _has_genuine_conflict(
        self,
        ranked: list[HypothesisCandidateResult],
    ) -> bool:
        """
        Return whether independent conflict-capable observations disagree.

        Broad ambiguous/contextual signals are intentionally excluded from
        hard contradiction detection.
        """

        conflicting_candidates = 0

        for candidate in ranked:
            if candidate.score < self._policy.conflict_threshold:
                continue

            has_conflict_eligible_support = any(
                observation.conflict_eligible
                and observation.polarity is ObservationPolarity.SUPPORT
                for observation in candidate.supporting_observations
            )

            if not has_conflict_eligible_support:
                continue

            conflicting_candidates += 1

            if conflicting_candidates >= 2:
                return True

        return False
