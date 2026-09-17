"""Profile evidence and intelligence analysis application service."""

from datetime import date

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.evidence import (
    BioBirthYearExtractor,
    Evidence,
    Fact,
    FactKind,
    FactResolver,
    UsernameBirthYearExtractor,
)
from veyra.domain.evidence.extractors import (
    BioRelationshipStatusExtractor,
)
from veyra.domain.intelligence import (
    HypothesisEvaluationService,
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
    HypothesisStrategyRegistry,
    RelationshipSignal,
    RelationshipSignalExtractor,
)
from veyra.domain.intelligence.relationship_strategy import (
    RELATIONSHIP_HYPOTHESIS_STRATEGY,
    RelationshipHypothesisAdapter,
)
from veyra.domain.snapshots import ProfileSnapshot
from veyra.domain.validation import (
    AdultAgeValidator,
    ValidationResult,
)


class ProfileAnalysisService:
    """
    Analyze one immutable public profile snapshot.

    Current capabilities:
    - birth-year extraction from username and biography
    - adult-age validation
    - multilingual explicit relationship-status extraction
    - contextual relationship-signal extraction
    - relationship fact resolution
    - relationship hypothesis inference through the generic intelligence
      engine

    The service remains an application-level orchestrator. Extraction,
    resolution, inference, and validation behavior stay inside their
    respective domain components.
    """

    def __init__(
        self,
        *,
        username_birth_year_extractor: UsernameBirthYearExtractor | None = None,
        bio_birth_year_extractor: BioBirthYearExtractor | None = None,
        bio_relationship_status_extractor: BioRelationshipStatusExtractor | None = None,
        relationship_signal_extractor: RelationshipSignalExtractor | None = None,
        relationship_hypothesis_adapter: RelationshipHypothesisAdapter | None = None,
        hypothesis_service: HypothesisEvaluationService | None = None,
        fact_resolver: FactResolver | None = None,
        adult_age_validator: AdultAgeValidator | None = None,
    ) -> None:
        self._username_birth_year_extractor = (
            username_birth_year_extractor
            if username_birth_year_extractor is not None
            else UsernameBirthYearExtractor()
        )

        self._bio_birth_year_extractor = (
            bio_birth_year_extractor
            if bio_birth_year_extractor is not None
            else BioBirthYearExtractor()
        )

        self._bio_relationship_status_extractor = (
            bio_relationship_status_extractor
            if bio_relationship_status_extractor is not None
            else BioRelationshipStatusExtractor()
        )

        self._relationship_signal_extractor = (
            relationship_signal_extractor
            if relationship_signal_extractor is not None
            else RelationshipSignalExtractor()
        )

        self._relationship_hypothesis_adapter = (
            relationship_hypothesis_adapter
            if relationship_hypothesis_adapter is not None
            else RelationshipHypothesisAdapter()
        )

        self._fact_resolver = fact_resolver if fact_resolver is not None else FactResolver()

        self._adult_age_validator = (
            adult_age_validator if adult_age_validator is not None else AdultAgeValidator()
        )

        self._hypothesis_service = (
            hypothesis_service
            if hypothesis_service is not None
            else HypothesisEvaluationService(
                registry=HypothesisStrategyRegistry((RELATIONSHIP_HYPOTHESIS_STRATEGY,))
            )
        )

    def analyze(
        self,
        snapshot: ProfileSnapshot,
        *,
        reference_date: date,
    ) -> ProfileAnalysisResult:
        """
        Analyze a snapshot and return one explainable intelligence result.

        ``reference_date`` remains explicit so analysis is deterministic and
        historically reproducible.
        """

        birth_year_evidence = self._extract_birth_year_evidence(
            snapshot,
        )

        relationship_evidence = self._extract_relationship_evidence(
            snapshot,
        )

        all_evidence = (
            *birth_year_evidence,
            *relationship_evidence,
        )

        birth_year_fact = self._fact_resolver.resolve(
            FactKind.BIRTH_YEAR,
            birth_year_evidence,
        )

        relationship_fact = self._fact_resolver.resolve(
            FactKind.RELATIONSHIP_STATUS,
            relationship_evidence,
        )

        facts: tuple[Fact, ...] = (
            birth_year_fact,
            relationship_fact,
        )

        relationship_observations = self._build_relationship_observations(
            snapshot=snapshot,
            relationship_fact=relationship_fact,
        )

        relationship_hypothesis = self._hypothesis_service.evaluate(
            HypothesisKind.RELATIONSHIP_STATUS,
            relationship_observations,
        )

        hypotheses: tuple[HypothesisResult, ...] = (relationship_hypothesis,)

        age_validation = self._adult_age_validator.validate(
            birth_year_fact,
            reference_date=reference_date,
        )

        validation = ValidationResult.combine((age_validation,))

        return ProfileAnalysisResult(
            snapshot_id=snapshot.id,
            profile_id=snapshot.profile_id,
            evidence=all_evidence,
            facts=facts,
            observations=relationship_observations,
            hypotheses=hypotheses,
            validation=validation,
        )

    def _extract_birth_year_evidence(
        self,
        snapshot: ProfileSnapshot,
    ) -> tuple[Evidence, ...]:
        """Extract all available birth-year evidence."""

        evidence: list[Evidence] = []

        evidence.extend(
            self._username_birth_year_extractor.extract(
                snapshot.username,
            )
        )

        if snapshot.bio is not None:
            evidence.extend(
                self._bio_birth_year_extractor.extract(
                    snapshot.bio,
                )
            )

        return tuple(
            evidence,
        )

    def _extract_relationship_evidence(
        self,
        snapshot: ProfileSnapshot,
    ) -> tuple[Evidence, ...]:
        """Extract explicit public relationship-status evidence."""

        if snapshot.bio is None:
            return ()

        return self._bio_relationship_status_extractor.extract(
            snapshot.bio,
        )

    def _build_relationship_observations(
        self,
        *,
        snapshot: ProfileSnapshot,
        relationship_fact: Fact,
    ) -> tuple[HypothesisObservation, ...]:
        """
        Build generic hypothesis observations from relationship intelligence.

        Explicit facts and contextual signals remain separate inputs before
        being normalized into generic inference observations.
        """

        signals: tuple[
            RelationshipSignal,
            ...,
        ] = ()

        if snapshot.bio is not None:
            signals = self._relationship_signal_extractor.extract(
                snapshot.bio,
            )

        return self._relationship_hypothesis_adapter.combine(
            fact=relationship_fact,
            signals=signals,
        )
