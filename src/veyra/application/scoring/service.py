"""Application orchestration for explainable profile scoring."""

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.scoring import (
    ScoreResult,
    WeightedScoringEngine,
)

from .adapter import AnalysisScoringFeatureAdapter
from .rules import AnalysisScoringPolicy


class ProfileScoringService:
    """
    Orchestrate analysis adaptation and deterministic score aggregation.

    The application layer owns composition while the domain scoring engine
    remains unaware of profile-analysis DTOs or scoring-policy rule types.
    """

    def __init__(
        self,
        *,
        feature_adapter: AnalysisScoringFeatureAdapter | None = None,
        scoring_engine: WeightedScoringEngine | None = None,
    ) -> None:
        self._feature_adapter = (
            feature_adapter if feature_adapter is not None else AnalysisScoringFeatureAdapter()
        )
        self._scoring_engine = (
            scoring_engine if scoring_engine is not None else WeightedScoringEngine()
        )

    def score(
        self,
        analysis: ProfileAnalysisResult,
        policy: AnalysisScoringPolicy,
    ) -> ScoreResult:
        """Return one explainable normalized score for a profile analysis."""

        features = self._feature_adapter.adapt(
            analysis,
            policy,
        )

        return self._scoring_engine.score(
            features,
        )
