"""Tests for analysis scoring rule definitions."""

import pytest

from veyra.application.scoring import (
    AnalysisScoringPolicy,
    EducationInstitutionScoringRule,
    FactValueScoringRule,
    HypothesisValueScoringRule,
)
from veyra.domain.evidence import FactKind
from veyra.domain.intelligence import HypothesisKind


def test_policy_rejects_duplicate_keys_across_rule_types() -> None:
    with pytest.raises(
        ValueError,
        match="scoring rule keys must be unique",
    ):
        AnalysisScoringPolicy(
            fact_rules=(
                FactValueScoringRule(
                    key="profile-match",
                    kind=FactKind.OCCUPATION,
                    accepted_values=("software engineer",),
                    weight=1.0,
                    reason="Occupation matches.",
                ),
            ),
            hypothesis_rules=(
                HypothesisValueScoringRule(
                    key="profile-match",
                    kind=HypothesisKind.PROFILE_PURPOSE,
                    accepted_values=("professional",),
                    weight=1.0,
                    reason="Profile purpose matches.",
                ),
            ),
        )


def test_fact_rule_requires_accepted_values() -> None:
    with pytest.raises(
        ValueError,
        match="accepted_values must not be empty",
    ):
        FactValueScoringRule(
            key="occupation",
            kind=FactKind.OCCUPATION,
            accepted_values=(),
            weight=1.0,
            reason="Occupation preference.",
        )


def test_hypothesis_rule_normalizes_accepted_values() -> None:
    rule = HypothesisValueScoringRule(
        key="purpose",
        kind=HypothesisKind.PROFILE_PURPOSE,
        accepted_values=(" professional ", "creator"),
        weight=1.0,
        reason="Purpose preference.",
    )

    assert rule.accepted_values == (
        "professional",
        "creator",
    )


def test_relation_rule_normalizes_pair_values() -> None:
    rule = EducationInstitutionScoringRule(
        key="education-pair",
        education=" MASTER:Data Science ",
        institution=" Stanford University ",
        weight=2.0,
        reason="Desired education path.",
    )

    assert rule.education == "master:data science"
    assert rule.institution == "stanford university"
