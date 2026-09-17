"""Adapters from profile-analysis semantics to normalized scoring features."""

from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.evidence import (
    Fact,
    FactCardinality,
    FactStatus,
)
from veyra.domain.intelligence import HypothesisStatus
from veyra.domain.scoring import (
    ScoringFeature,
    ScoringSourceKind,
)

from .rules import (
    AnalysisScoringPolicy,
    EducationInstitutionScoringRule,
    FactValueScoringRule,
    HypothesisValueScoringRule,
)


class AnalysisScoringFeatureAdapter:
    """
    Convert analysis results into rule-driven normalized scoring features.

    Missing or unresolved information is omitted rather than treated as
    negative evidence. A supported source that explicitly does not match a
    configured rule produces a value of zero.
    """

    def adapt(
        self,
        analysis: ProfileAnalysisResult,
        policy: AnalysisScoringPolicy,
    ) -> tuple[ScoringFeature, ...]:
        """Build deterministic scoring features for one analysis result."""

        features: list[ScoringFeature] = []

        for fact_rule in policy.fact_rules:
            feature = self._from_fact_rule(
                analysis,
                fact_rule,
            )

            if feature is not None:
                features.append(
                    feature,
                )

        for hypothesis_rule in policy.hypothesis_rules:
            feature = self._from_hypothesis_rule(
                analysis,
                hypothesis_rule,
            )

            if feature is not None:
                features.append(
                    feature,
                )

        for relation_rule in policy.relation_rules:
            feature = self._from_relation_rule(
                analysis,
                relation_rule,
            )

            if feature is not None:
                features.append(
                    feature,
                )

        return tuple(
            sorted(
                features,
                key=lambda feature: feature.key,
            )
        )

    @staticmethod
    def _from_fact_rule(
        analysis: ProfileAnalysisResult,
        rule: FactValueScoringRule,
    ) -> ScoringFeature | None:
        """Adapt one resolved fact into a scoring feature."""

        fact = analysis.fact_for(
            rule.kind,
        )

        if fact is None:
            return None

        if fact.status is not FactStatus.SUPPORTED:
            return None

        values = AnalysisScoringFeatureAdapter._fact_values(
            fact,
        )

        matched = any(value in rule.accepted_values for value in values)

        return ScoringFeature(
            key=rule.key,
            value=1.0 if matched else 0.0,
            weight=rule.weight,
            confidence=fact.confidence,
            reason=rule.reason,
            source_kind=ScoringSourceKind.FACT,
            source_key=f"fact:{rule.kind.value}",
        )

    @staticmethod
    def _fact_values(
        fact: Fact,
    ) -> tuple[object, ...]:
        """Return normalized resolved values independent of fact cardinality."""

        if fact.cardinality is FactCardinality.MULTIPLE:
            return tuple(
                fact.values,
            )

        if fact.value is None:
            return ()

        return (fact.value,)

    @staticmethod
    def _from_hypothesis_rule(
        analysis: ProfileAnalysisResult,
        rule: HypothesisValueScoringRule,
    ) -> ScoringFeature | None:
        """Adapt one hypothesis candidate score into a scoring feature."""

        hypothesis = analysis.hypothesis_for(
            rule.kind,
        )

        if hypothesis is None:
            return None

        if hypothesis.status is HypothesisStatus.UNKNOWN:
            return None

        matched_scores = tuple(
            candidate.score
            for value in rule.accepted_values
            if (
                candidate := hypothesis.candidate_for(
                    value,
                )
            )
            is not None
        )

        value = max(
            matched_scores,
            default=0.0,
        )

        return ScoringFeature(
            key=rule.key,
            value=value,
            weight=rule.weight,
            confidence=hypothesis.confidence,
            reason=rule.reason,
            source_kind=ScoringSourceKind.HYPOTHESIS,
            source_key=f"hypothesis:{rule.kind.value}",
        )

    @staticmethod
    def _from_relation_rule(
        analysis: ProfileAnalysisResult,
        rule: EducationInstitutionScoringRule,
    ) -> ScoringFeature | None:
        """Adapt explicit education/institution relations into one feature."""

        relations = analysis.education_institution_relations

        if not relations:
            return None

        matching_relations = tuple(
            relation
            for relation in relations
            if (
                relation.education.casefold() == rule.education
                and relation.institution.casefold() == rule.institution
            )
        )

        if matching_relations:
            confidence = max(relation.confidence for relation in matching_relations)
            value = 1.0
        else:
            confidence = max(relation.confidence for relation in relations)
            value = 0.0

        return ScoringFeature(
            key=rule.key,
            value=value,
            weight=rule.weight,
            confidence=confidence,
            reason=rule.reason,
            source_kind=ScoringSourceKind.RELATION,
            source_key="relation:education_institution",
        )
