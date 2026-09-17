"""Deterministic weighted scoring engine."""

from collections.abc import Iterable

from .entities import (
    ScoreContribution,
    ScoreResult,
    ScoringFeature,
)


class WeightedScoringEngine:
    """
    Aggregate normalized feature values into an explainable 0-10 score.

    Confidence scales feature influence rather than directly lowering the
    candidate score:

        effective_weight = configured_weight * confidence
        normalized_score = sum(value * effective_weight) / sum(effective_weight)

    This keeps uncertain evidence weak instead of treating uncertainty as
    negative evidence.
    """

    algorithm_version = "scoring-v1"

    def score(
        self,
        features: Iterable[ScoringFeature],
    ) -> ScoreResult:
        """Return a deterministic explainable score for normalized features."""

        ordered_features = tuple(
            sorted(
                features,
                key=lambda feature: feature.key,
            )
        )

        self._validate_unique_keys(
            ordered_features,
        )

        contributions = tuple(
            self._to_contribution(
                feature,
            )
            for feature in ordered_features
        )

        total_effective_weight = sum(
            contribution.effective_weight for contribution in contributions
        )

        if total_effective_weight == 0:
            return ScoreResult(
                score=None,
                normalized_value=None,
                total_effective_weight=0.0,
                contributions=contributions,
                algorithm_version=self.algorithm_version,
            )

        weighted_total = sum(contribution.weighted_value for contribution in contributions)

        normalized_value = weighted_total / total_effective_weight
        score = normalized_value * 10

        return ScoreResult(
            score=round(
                score,
                6,
            ),
            normalized_value=round(
                normalized_value,
                6,
            ),
            total_effective_weight=round(
                total_effective_weight,
                6,
            ),
            contributions=contributions,
            algorithm_version=self.algorithm_version,
        )

    @staticmethod
    def _validate_unique_keys(
        features: tuple[ScoringFeature, ...],
    ) -> None:
        """Reject duplicate feature keys to prevent accidental double counting."""

        seen: set[str] = set()

        for feature in features:
            if feature.key in seen:
                raise ValueError(
                    f"Duplicate scoring feature key: {feature.key}.",
                )

            seen.add(
                feature.key,
            )

    @staticmethod
    def _to_contribution(
        feature: ScoringFeature,
    ) -> ScoreContribution:
        """Convert one normalized feature into an explainable contribution."""

        return ScoreContribution(
            key=feature.key,
            value=feature.value,
            configured_weight=feature.weight,
            confidence=feature.confidence,
            effective_weight=round(
                feature.effective_weight,
                6,
            ),
            weighted_value=round(
                feature.weighted_value,
                6,
            ),
            reason=feature.reason,
            source_kind=feature.source_kind,
            source_key=feature.source_key,
        )
