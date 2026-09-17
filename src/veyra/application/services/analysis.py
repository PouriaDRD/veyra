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
    BioLocationExtractor,
    BioRelationshipStatusExtractor,
)
from veyra.domain.intelligence import (
    HypothesisEvaluationService,
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
    HypothesisStrategyRegistry,
    LocationSignal,
    RelationshipSignal,
    RelationshipSignalExtractor,
)
from veyra.domain.intelligence.location_signal_extractor import (
    BioLocationSignalExtractor,
)
from veyra.domain.intelligence.location_strategy import (
    LIKELY_LOCATION_HYPOTHESIS_STRATEGY,
    LocationHypothesisAdapter,
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
    - birth-year extraction and adult-age validation
    - multilingual relationship fact extraction
    - contextual relationship inference
    - multilingual explicit city/country extraction
    - contextual biography location signals
    - likely-location inference through the generic hypothesis engine

    Facts, contextual signals, hypotheses, and validation findings remain
    semantically separate throughout the pipeline.
    """

    def __init__(
        self,
        *,
        username_birth_year_extractor: UsernameBirthYearExtractor | None = None,
        bio_birth_year_extractor: BioBirthYearExtractor | None = None,
        bio_relationship_status_extractor: BioRelationshipStatusExtractor | None = None,
        relationship_signal_extractor: RelationshipSignalExtractor | None = None,
        relationship_hypothesis_adapter: RelationshipHypothesisAdapter | None = None,
        bio_location_extractor: BioLocationExtractor | None = None,
        bio_location_signal_extractor: BioLocationSignalExtractor | None = None,
        location_hypothesis_adapter: LocationHypothesisAdapter | None = None,
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

        self._bio_location_extractor = (
            bio_location_extractor if bio_location_extractor is not None else BioLocationExtractor()
        )

        self._bio_location_signal_extractor = (
            bio_location_signal_extractor
            if bio_location_signal_extractor is not None
            else BioLocationSignalExtractor()
        )

        self._location_hypothesis_adapter = (
            location_hypothesis_adapter
            if location_hypothesis_adapter is not None
            else LocationHypothesisAdapter()
        )

        self._fact_resolver = fact_resolver if fact_resolver is not None else FactResolver()

        self._adult_age_validator = (
            adult_age_validator if adult_age_validator is not None else AdultAgeValidator()
        )

        self._hypothesis_service = (
            hypothesis_service
            if hypothesis_service is not None
            else HypothesisEvaluationService(
                registry=HypothesisStrategyRegistry(
                    (
                        RELATIONSHIP_HYPOTHESIS_STRATEGY,
                        LIKELY_LOCATION_HYPOTHESIS_STRATEGY,
                    )
                )
            )
        )

    def analyze(
        self,
        snapshot: ProfileSnapshot,
        *,
        reference_date: date,
    ) -> ProfileAnalysisResult:
        """Analyze a snapshot and return one explainable intelligence result."""

        birth_year_evidence = self._extract_birth_year_evidence(
            snapshot,
        )

        relationship_evidence = self._extract_relationship_evidence(
            snapshot,
        )

        city_evidence = self._extract_location_evidence(
            snapshot,
            kind=FactKind.CITY,
        )

        country_evidence = self._extract_location_evidence(
            snapshot,
            kind=FactKind.COUNTRY,
        )

        all_evidence = (
            *birth_year_evidence,
            *relationship_evidence,
            *city_evidence,
            *country_evidence,
        )

        birth_year_fact = self._fact_resolver.resolve(
            FactKind.BIRTH_YEAR,
            birth_year_evidence,
        )

        relationship_fact = self._fact_resolver.resolve(
            FactKind.RELATIONSHIP_STATUS,
            relationship_evidence,
        )

        city_fact = self._fact_resolver.resolve(
            FactKind.CITY,
            city_evidence,
        )

        country_fact = self._fact_resolver.resolve(
            FactKind.COUNTRY,
            country_evidence,
        )

        facts: tuple[Fact, ...] = (
            birth_year_fact,
            relationship_fact,
            city_fact,
            country_fact,
        )

        relationship_observations = self._build_relationship_observations(
            snapshot=snapshot,
            relationship_fact=relationship_fact,
        )

        location_observations = self._build_location_observations(
            snapshot=snapshot,
            city_fact=city_fact,
        )

        observations = (
            *relationship_observations,
            *location_observations,
        )

        relationship_hypothesis = self._hypothesis_service.evaluate(
            HypothesisKind.RELATIONSHIP_STATUS,
            relationship_observations,
        )

        location_hypothesis = self._hypothesis_service.evaluate(
            HypothesisKind.LIKELY_LOCATION,
            location_observations,
        )

        hypotheses: tuple[HypothesisResult, ...] = (
            relationship_hypothesis,
            location_hypothesis,
        )

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
            observations=observations,
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

    def _extract_location_evidence(
        self,
        snapshot: ProfileSnapshot,
        *,
        kind: FactKind,
    ) -> tuple[Evidence, ...]:
        """Extract explicit CITY or COUNTRY evidence."""

        if snapshot.bio is None:
            return ()

        return self._bio_location_extractor.extract_for_kind(
            snapshot.bio,
            kind=kind,
        )

    def _build_relationship_observations(
        self,
        *,
        snapshot: ProfileSnapshot,
        relationship_fact: Fact,
    ) -> tuple[HypothesisObservation, ...]:
        """Build relationship hypothesis observations."""

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

    def _build_location_observations(
        self,
        *,
        snapshot: ProfileSnapshot,
        city_fact: Fact,
    ) -> tuple[HypothesisObservation, ...]:
        """Build likely-location hypothesis observations."""

        signals: tuple[
            LocationSignal,
            ...,
        ] = ()

        if snapshot.bio is not None:
            signals = self._bio_location_signal_extractor.extract(
                snapshot.bio,
            )

        return self._location_hypothesis_adapter.combine(
            city_fact=city_fact,
            signals=signals,
        )
