"""Iran-focused candidate eligibility decisions."""

from dataclasses import dataclass
from enum import StrEnum

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.evidence import (
    DeclaredGender,
    FactKind,
    FactStatus,
)
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisStatus,
    ProfilePurpose,
)


class CandidateEligibilityStatus(StrEnum):
    """Outcome of candidate eligibility evaluation."""

    ELIGIBLE = "eligible"
    ENRICHMENT_REQUIRED = "enrichment_required"
    REJECTED = "rejected"


class CandidateEligibilityReason(StrEnum):
    """Machine-readable reason contributing to an eligibility decision."""

    PUBLIC_PROFILE = "public_profile"
    PRIVACY_UNKNOWN = "privacy_unknown"
    ADULT_NOT_CONFIRMED = "adult_not_confirmed"
    BUSINESS_PROFILE = "business_profile"
    ORGANIZATION_PROFILE = "organization_profile"
    FEMALE_DECLARED = "female_declared"
    MALE_DECLARED = "male_declared"
    GENDER_UNKNOWN = "gender_unknown"
    GENDER_CONFLICTED = "gender_conflicted"


@dataclass(frozen=True, slots=True)
class CandidateEligibilityResult:
    """Explainable candidate-eligibility decision."""

    status: CandidateEligibilityStatus
    reasons: tuple[CandidateEligibilityReason, ...]

    @property
    def is_eligible(self) -> bool:
        """Return whether the candidate may proceed to scoring."""

        return self.status is CandidateEligibilityStatus.ELIGIBLE


class CandidateEligibilityService:
    """
    Evaluate core private/adult/personal/female candidate eligibility.

    Unknown gender is preserved for enrichment instead of being treated as
    female or permanently discarded.
    """

    def evaluate(
        self,
        analysis: ProfileAnalysisResult,
    ) -> CandidateEligibilityResult:
        """Return one deterministic eligibility result."""

        if analysis.is_private is False:
            return self._result(
                CandidateEligibilityStatus.REJECTED,
                CandidateEligibilityReason.PUBLIC_PROFILE,
            )

        if analysis.is_private is None:
            return self._result(
                CandidateEligibilityStatus.ENRICHMENT_REQUIRED,
                CandidateEligibilityReason.PRIVACY_UNKNOWN,
            )

        if not analysis.validation.is_accepted:
            return self._result(
                CandidateEligibilityStatus.REJECTED,
                CandidateEligibilityReason.ADULT_NOT_CONFIRMED,
            )

        purpose_rejection = self._purpose_rejection(
            analysis,
        )

        if purpose_rejection is not None:
            return self._result(
                CandidateEligibilityStatus.REJECTED,
                purpose_rejection,
            )

        gender_fact = analysis.fact_for(
            FactKind.DECLARED_GENDER,
        )

        if gender_fact is None or gender_fact.status is FactStatus.UNKNOWN:
            return self._result(
                CandidateEligibilityStatus.ENRICHMENT_REQUIRED,
                CandidateEligibilityReason.GENDER_UNKNOWN,
            )

        if gender_fact.status is FactStatus.CONFLICTED:
            return self._result(
                CandidateEligibilityStatus.ENRICHMENT_REQUIRED,
                CandidateEligibilityReason.GENDER_CONFLICTED,
            )

        if gender_fact.value == DeclaredGender.MALE.value:
            return self._result(
                CandidateEligibilityStatus.REJECTED,
                CandidateEligibilityReason.MALE_DECLARED,
            )

        if gender_fact.value == DeclaredGender.FEMALE.value:
            return self._result(
                CandidateEligibilityStatus.ELIGIBLE,
                CandidateEligibilityReason.FEMALE_DECLARED,
            )

        return self._result(
            CandidateEligibilityStatus.ENRICHMENT_REQUIRED,
            CandidateEligibilityReason.GENDER_UNKNOWN,
        )

    @staticmethod
    def _purpose_rejection(
        analysis: ProfileAnalysisResult,
    ) -> CandidateEligibilityReason | None:
        """Reject strongly supported business/organization profiles."""

        purpose = analysis.hypothesis_for(
            HypothesisKind.PROFILE_PURPOSE,
        )

        if purpose is None:
            return None

        if purpose.status not in {
            HypothesisStatus.PROBABLE,
            HypothesisStatus.STRONGLY_SUPPORTED,
        }:
            return None

        if purpose.best_value == ProfilePurpose.BUSINESS.value:
            return CandidateEligibilityReason.BUSINESS_PROFILE

        if purpose.best_value == ProfilePurpose.ORGANIZATION.value:
            return CandidateEligibilityReason.ORGANIZATION_PROFILE

        return None

    @staticmethod
    def _result(
        status: CandidateEligibilityStatus,
        reason: CandidateEligibilityReason,
    ) -> CandidateEligibilityResult:
        """Construct a single-reason deterministic result."""

        return CandidateEligibilityResult(
            status=status,
            reasons=(reason,),
        )
