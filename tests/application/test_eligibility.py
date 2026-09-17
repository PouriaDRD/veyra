"""Tests for Iran-focused candidate eligibility evaluation."""

from dataclasses import replace
from uuid import uuid4

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.application.eligibility import (
    CandidateEligibilityReason,
    CandidateEligibilityService,
    CandidateEligibilityStatus,
)
from veyra.domain.evidence import (
    DeclaredGender,
    Evidence,
    EvidenceSource,
    Fact,
    FactKind,
    FactStatus,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    HypothesisCandidateResult,
    HypothesisKind,
    HypothesisResult,
    HypothesisStatus,
    ProfilePurpose,
)
from veyra.domain.validation import (
    ValidationCode,
    ValidationFinding,
    ValidationResult,
    ValidationSeverity,
)


def adult_validation() -> ValidationResult:
    return ValidationResult(
        findings=(
            ValidationFinding(
                code=ValidationCode.AGE_CONFIRMED_ADULT,
                severity=ValidationSeverity.INFO,
                message="Adult confirmed.",
                confidence=0.95,
            ),
        )
    )


def declared_gender_fact(
    gender: DeclaredGender,
) -> Fact:
    evidence = Evidence(
        source=EvidenceSource.BIO,
        raw_value=gender.value,
        normalized_value=gender.value,
        confidence=0.99,
        extractor="test",
        nature=EvidenceNature.EXPLICIT,
        strength=EvidenceStrength.VERY_STRONG,
    )

    return Fact(
        kind=FactKind.DECLARED_GENDER,
        status=FactStatus.SUPPORTED,
        confidence=0.99,
        value=gender.value,
        evidence=(evidence,),
    )


def base_analysis() -> ProfileAnalysisResult:
    return ProfileAnalysisResult(
        snapshot_id=uuid4(),
        profile_id=uuid4(),
        evidence=(),
        facts=(
            declared_gender_fact(
                DeclaredGender.FEMALE,
            ),
        ),
        observations=(),
        hypotheses=(),
        validation=adult_validation(),
        is_private=True,
    )


def test_confirmed_private_adult_declared_female_is_eligible() -> None:
    result = CandidateEligibilityService().evaluate(
        base_analysis(),
    )

    assert result.status is CandidateEligibilityStatus.ELIGIBLE
    assert result.reasons == (CandidateEligibilityReason.FEMALE_DECLARED,)


def test_declared_male_is_rejected() -> None:
    analysis = replace(
        base_analysis(),
        facts=(
            declared_gender_fact(
                DeclaredGender.MALE,
            ),
        ),
    )

    result = CandidateEligibilityService().evaluate(
        analysis,
    )

    assert result.status is CandidateEligibilityStatus.REJECTED
    assert result.reasons == (CandidateEligibilityReason.MALE_DECLARED,)


def test_unknown_gender_requires_enrichment() -> None:
    analysis = replace(
        base_analysis(),
        facts=(),
    )

    result = CandidateEligibilityService().evaluate(
        analysis,
    )

    assert result.status is CandidateEligibilityStatus.ENRICHMENT_REQUIRED
    assert result.reasons == (CandidateEligibilityReason.GENDER_UNKNOWN,)


def test_public_profile_is_rejected_before_gender_decision() -> None:
    analysis = replace(
        base_analysis(),
        is_private=False,
    )

    result = CandidateEligibilityService().evaluate(
        analysis,
    )

    assert result.status is CandidateEligibilityStatus.REJECTED
    assert result.reasons == (CandidateEligibilityReason.PUBLIC_PROFILE,)


def test_strong_business_profile_is_rejected() -> None:
    business = HypothesisResult(
        kind=HypothesisKind.PROFILE_PURPOSE,
        status=HypothesisStatus.PROBABLE,
        best_value=ProfilePurpose.BUSINESS.value,
        confidence=0.8,
        candidates=(
            HypothesisCandidateResult(
                value=ProfilePurpose.UNKNOWN.value,
                score=0.0,
                support=0.0,
                opposition=0.0,
            ),
            HypothesisCandidateResult(
                value=ProfilePurpose.BUSINESS.value,
                score=0.8,
                support=0.8,
                opposition=0.0,
            ),
        ),
        algorithm_version="test-v1",
    )

    analysis = replace(
        base_analysis(),
        hypotheses=(business,),
    )

    result = CandidateEligibilityService().evaluate(
        analysis,
    )

    assert result.status is CandidateEligibilityStatus.REJECTED
    assert result.reasons == (CandidateEligibilityReason.BUSINESS_PROFILE,)


def test_unconfirmed_adult_is_rejected() -> None:
    analysis = replace(
        base_analysis(),
        validation=ValidationResult(
            findings=(
                ValidationFinding(
                    code=ValidationCode.AGE_UNCERTAIN,
                    severity=ValidationSeverity.REJECT,
                    message="Adult age could not be established.",
                    confidence=0.0,
                ),
            )
        ),
    )

    result = CandidateEligibilityService().evaluate(
        analysis,
    )

    assert result.status is CandidateEligibilityStatus.REJECTED
    assert result.reasons == (CandidateEligibilityReason.ADULT_NOT_CONFIRMED,)
