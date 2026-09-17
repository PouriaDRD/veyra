"""Profile evidence analysis application service."""

from datetime import date

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.evidence import (
    BioBirthYearExtractor,
    Evidence,
    FactKind,
    FactResolver,
    UsernameBirthYearExtractor,
)
from veyra.domain.snapshots import ProfileSnapshot
from veyra.domain.validation import (
    AdultAgeValidator,
    ValidationResult,
)


class ProfileAnalysisService:
    """
    Analyze one immutable profile snapshot.

    Current analysis scope:
    - extract explicit birth-year evidence from username
    - extract explicit birth-year evidence from biography
    - resolve ambiguity and contradictions
    - validate the adult-age requirement

    Additional extractors, fact kinds, and validators can be composed here
    later without coupling provider or presentation code to domain details.
    """

    def __init__(
        self,
        *,
        username_birth_year_extractor: UsernameBirthYearExtractor | None = None,
        bio_birth_year_extractor: BioBirthYearExtractor | None = None,
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

        self._fact_resolver = fact_resolver if fact_resolver is not None else FactResolver()

        self._adult_age_validator = (
            adult_age_validator if adult_age_validator is not None else AdultAgeValidator()
        )

    def analyze(
        self,
        snapshot: ProfileSnapshot,
        *,
        reference_date: date,
    ) -> ProfileAnalysisResult:
        """
        Analyze a snapshot and return an explainable result.

        ``reference_date`` is explicit so analysis remains deterministic
        and historically reproducible.
        """

        birth_year_evidence = self._extract_birth_year_evidence(
            snapshot,
        )

        birth_year_fact = self._fact_resolver.resolve(
            FactKind.BIRTH_YEAR,
            birth_year_evidence,
        )

        age_validation = self._adult_age_validator.validate(
            birth_year_fact,
            reference_date=reference_date,
        )

        validation = ValidationResult.combine((age_validation,))

        return ProfileAnalysisResult(
            snapshot_id=snapshot.id,
            profile_id=snapshot.profile_id,
            evidence=birth_year_evidence,
            facts=(birth_year_fact,),
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

        return tuple(evidence)
