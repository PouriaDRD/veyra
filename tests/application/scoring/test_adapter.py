"""Tests for profile-analysis to scoring-feature adapters."""

from dataclasses import replace
from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.application.scoring import (
    AnalysisScoringFeatureAdapter,
    AnalysisScoringPolicy,
    EducationInstitutionScoringRule,
    FactValueScoringRule,
    HypothesisValueScoringRule,
)
from veyra.domain.evidence import FactKind
from veyra.domain.intelligence import (
    HypothesisCandidateResult,
    HypothesisKind,
    HypothesisResult,
    HypothesisStatus,
)
from veyra.domain.scoring import ScoringSourceKind
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def analyze(
    bio: str | None,
) -> ProfileAnalysisResult:
    """Analyze one deterministic adult profile."""

    return ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="scoring_adapter_1997",
            display_name=None,
            bio=bio,
        ),
        reference_date=REFERENCE_DATE,
    )


def test_fact_rule_scores_matching_supported_scalar_fact() -> None:
    analysis = analyze(
        "Software Engineer",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="occupation-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("software engineer",),
                    weight=2.0,
                    reason="Desired occupation.",
                ),
            ),
        ),
    )

    assert len(features) == 1

    feature = features[0]

    assert feature.key == "occupation-match"
    assert feature.value == 1.0
    assert feature.weight == 2.0
    assert feature.source_kind is ScoringSourceKind.FACT
    assert feature.source_key == "fact:occupation"


def test_fact_rule_scores_explicit_supported_mismatch_as_zero() -> None:
    analysis = analyze(
        "Software Engineer",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="occupation-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("doctor",),
                    weight=1.0,
                    reason="Desired occupation.",
                ),
            ),
        ),
    )

    assert len(features) == 1
    assert features[0].value == 0.0


def test_unknown_fact_is_omitted_instead_of_scored_as_negative() -> None:
    analysis = analyze(
        None,
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="employer-match",
                    kind=FactKind.EMPLOYER,
                    accepted_values=("openai",),
                    weight=1.0,
                    reason="Desired employer.",
                ),
            ),
        ),
    )

    assert features == ()


def test_multi_value_fact_matches_any_accepted_value() -> None:
    analysis = analyze(
        "BSc Computer Science | MSc Data Science",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="education-match",
                    kind=FactKind.EDUCATION,
                    accepted_values=("master:data science",),
                    weight=1.5,
                    reason="Desired education.",
                ),
            ),
        ),
    )

    assert len(features) == 1
    assert features[0].value == 1.0
    assert features[0].source_key == "fact:education"


def test_hypothesis_rule_uses_target_candidate_score_and_confidence() -> None:
    analysis = analyze(
        None,
    )

    hypothesis = HypothesisResult(
        kind=HypothesisKind.PROFILE_PURPOSE,
        status=HypothesisStatus.PROBABLE,
        best_value="professional",
        confidence=0.8,
        candidates=(
            HypothesisCandidateResult(
                value="unknown",
                score=0.0,
                support=0.0,
                opposition=0.0,
            ),
            HypothesisCandidateResult(
                value="professional",
                score=0.75,
                support=0.75,
                opposition=0.0,
            ),
            HypothesisCandidateResult(
                value="creator",
                score=0.2,
                support=0.2,
                opposition=0.0,
            ),
        ),
        algorithm_version="test-v1",
    )

    analysis = replace(
        analysis,
        hypotheses=(hypothesis,),
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            hypothesis_rules=(
                HypothesisValueScoringRule(
                    key="purpose-match",
                    kind=HypothesisKind.PROFILE_PURPOSE,
                    accepted_values=("professional",),
                    weight=2.0,
                    reason="Desired profile purpose.",
                ),
            ),
        ),
    )

    assert len(features) == 1

    feature = features[0]

    assert feature.value == 0.75
    assert feature.confidence == 0.8
    assert feature.source_kind is ScoringSourceKind.HYPOTHESIS
    assert feature.source_key == "hypothesis:profile_purpose"


def test_unknown_hypothesis_is_omitted() -> None:
    analysis = analyze(
        None,
    )

    hypothesis = HypothesisResult(
        kind=HypothesisKind.PROFILE_PURPOSE,
        status=HypothesisStatus.UNKNOWN,
        best_value="unknown",
        confidence=0.0,
        candidates=(
            HypothesisCandidateResult(
                value="unknown",
                score=0.0,
                support=0.0,
                opposition=0.0,
            ),
        ),
        algorithm_version="test-v1",
    )

    analysis = replace(
        analysis,
        hypotheses=(hypothesis,),
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            hypothesis_rules=(
                HypothesisValueScoringRule(
                    key="purpose-match",
                    kind=HypothesisKind.PROFILE_PURPOSE,
                    accepted_values=("professional",),
                    weight=1.0,
                    reason="Desired profile purpose.",
                ),
            ),
        ),
    )

    assert features == ()


def test_relation_rule_scores_matching_explicit_pair() -> None:
    analysis = analyze(
        "BSc Computer Science at MIT",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            relation_rules=(
                EducationInstitutionScoringRule(
                    key="education-pair",
                    education="bachelor:computer science",
                    institution="mit",
                    weight=2.0,
                    reason="Desired education and institution pair.",
                ),
            ),
        ),
    )

    assert len(features) == 1

    feature = features[0]

    assert feature.value == 1.0
    assert feature.confidence == 0.97
    assert feature.source_kind is ScoringSourceKind.RELATION
    assert feature.source_key == "relation:education_institution"


def test_relation_rule_scores_observed_mismatch_as_zero() -> None:
    analysis = analyze(
        "BSc Computer Science at MIT",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            relation_rules=(
                EducationInstitutionScoringRule(
                    key="education-pair",
                    education="bachelor:computer science",
                    institution="stanford university",
                    weight=2.0,
                    reason="Desired education and institution pair.",
                ),
            ),
        ),
    )

    assert len(features) == 1
    assert features[0].value == 0.0


def test_missing_relation_data_is_omitted() -> None:
    analysis = analyze(
        "BSc Computer Science | Student at MIT",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            relation_rules=(
                EducationInstitutionScoringRule(
                    key="education-pair",
                    education="bachelor:computer science",
                    institution="mit",
                    weight=2.0,
                    reason="Desired education and institution pair.",
                ),
            ),
        ),
    )

    assert features == ()


def test_adapter_returns_features_in_deterministic_key_order() -> None:
    analysis = analyze(
        "Software Engineer | BSc Computer Science at MIT",
    )

    features = AnalysisScoringFeatureAdapter().adapt(
        analysis,
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="z-occupation",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("software engineer",),
                    weight=1.0,
                    reason="Desired occupation.",
                ),
            ),
            relation_rules=(
                EducationInstitutionScoringRule(
                    key="a-education",
                    education="bachelor:computer science",
                    institution="mit",
                    weight=1.0,
                    reason="Desired education pair.",
                ),
            ),
        ),
    )

    assert tuple(feature.key for feature in features) == (
        "a-education",
        "z-occupation",
    )
