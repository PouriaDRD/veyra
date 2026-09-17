"""Application orchestration for explainable profile scoring."""

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.application.eligibility import CandidateEligibilityService
from veyra.domain.scoring import (
    ScoreResult,
    WeightedScoringEngine,
)

from .adapter import AnalysisScoringFeatureAdapter
from .rules import AnalysisScoringPolicy


class ProfileScoringService:
    """
    Orchestrate eligibility, analysis adaptation, and deterministic scoring.

    Candidate eligibility is a hard precondition. Ineligible or enrichment-only
    analyses are unscorable and never reach weighted feature aggregation.
    """

    def __init__(
        self,
        *,
        eligibility_service: CandidateEligibilityService | None = None,
        feature_adapter: AnalysisScoringFeatureAdapter | None = None,
        scoring_engine: WeightedScoringEngine | None = None,
    ) -> None:
        self._eligibility_service = (
            eligibility_service
            if eligibility_service is not None
            else CandidateEligibilityService()
        )
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
        """Return one explainable normalized score for an eligible analysis."""

        eligibility = self._eligibility_service.evaluate(
            analysis,
        )

        if not eligibility.is_eligible:
            return self._scoring_engine.score(
                (),
            )

        features = self._feature_adapter.adapt(
            analysis,
            policy,
        )

        return self._scoring_engine.score(
            features,
        )
