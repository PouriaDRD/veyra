"""Tests for relationship hypothesis adapter integration."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    Fact,
    FactKind,
    FactStatus,
)
from veyra.domain.intelligence import (
    HypothesisEvaluationService,
    HypothesisKind,
    HypothesisStatus,
    HypothesisStrategyRegistry,
    RelationshipSignal,
    RelationshipSignalKind,
    RelationshipStatus,
)
from veyra.domain.intelligence.relationship_strategy import (
    RELATIONSHIP_HYPOTHESIS_STRATEGY,
    RelationshipHypothesisAdapter,
    build_relationship_fact,
)


def build_explicit_evidence(
    value: RelationshipStatus,
    confidence: float = 0.98,
) -> Evidence:
    """Create explicit relationship evidence."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value=value.value,
        normalized_value=value.value,
        confidence=confidence,
    )


def build_service() -> HypothesisEvaluationService:
    """Create relationship-enabled hypothesis service."""

    return HypothesisEvaluationService(
        registry=HypothesisStrategyRegistry((RELATIONSHIP_HYPOTHESIS_STRATEGY,))
    )


def test_explicit_married_fact_becomes_strong_hypothesis() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.MARRIED,
            ),
        )
    )

    observations = RelationshipHypothesisAdapter().from_fact(
        fact,
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    assert result.best_value == RelationshipStatus.MARRIED.value

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_explicit_single_fact_becomes_strong_hypothesis() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.SINGLE,
            ),
        )
    )

    observations = RelationshipHypothesisAdapter().from_fact(
        fact,
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    assert result.best_value == RelationshipStatus.SINGLE.value


def test_plain_ring_supports_non_single_candidates_only() -> None:
    signal = RelationshipSignal(
        kind=RelationshipSignalKind.RING_EMOJI,
        raw_value="💍",
        weight=0.45,
    )

    observations = RelationshipHypothesisAdapter().from_signals((signal,))

    targets = {observation.target_value for observation in observations}

    assert targets == {
        RelationshipStatus.MARRIED.value,
        RelationshipStatus.ENGAGED.value,
        RelationshipStatus.IN_RELATIONSHIP.value,
    }

    assert RelationshipStatus.SINGLE.value not in targets


def test_name_adjacent_ring_is_stronger_than_plain_heart() -> None:
    adapter = RelationshipHypothesisAdapter()

    ring = adapter.from_signals(
        (
            RelationshipSignal(
                kind=RelationshipSignalKind.NAME_ADJACENT_RING,
                raw_value="Sara 💍",
                weight=0.60,
            ),
        )
    )

    heart = adapter.from_signals(
        (
            RelationshipSignal(
                kind=RelationshipSignalKind.RED_HEART_EMOJI,
                raw_value="❤️",
                weight=0.18,
            ),
        )
    )

    assert ring[0].weight > heart[0].weight


def test_explicit_single_remains_stronger_than_contextual_ring() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.SINGLE,
            ),
        )
    )

    signals = (
        RelationshipSignal(
            kind=RelationshipSignalKind.RING_EMOJI,
            raw_value="💍",
            weight=0.45,
        ),
    )

    observations = RelationshipHypothesisAdapter().combine(
        fact=fact,
        signals=signals,
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    single = result.candidate_for(RelationshipStatus.SINGLE.value)

    married = result.candidate_for(RelationshipStatus.MARRIED.value)

    assert single is not None
    assert married is not None

    assert single.score > married.score

    assert result.best_value == RelationshipStatus.SINGLE.value


def test_conflicting_explicit_facts_are_preserved() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.SINGLE,
            ),
            build_explicit_evidence(
                RelationshipStatus.MARRIED,
            ),
        )
    )

    assert fact.status is FactStatus.CONFLICTED

    observations = RelationshipHypothesisAdapter().from_fact(
        fact,
    )

    targets = {observation.target_value for observation in observations}

    assert targets == {
        RelationshipStatus.SINGLE.value,
        RelationshipStatus.MARRIED.value,
    }


def test_conflicting_explicit_facts_produce_conflicted_hypothesis() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.SINGLE,
            ),
            build_explicit_evidence(
                RelationshipStatus.MARRIED,
            ),
        )
    )

    observations = RelationshipHypothesisAdapter().from_fact(
        fact,
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    assert result.status is HypothesisStatus.CONFLICTED


def test_unknown_fact_produces_no_observations() -> None:
    fact = Fact(
        kind=FactKind.RELATIONSHIP_STATUS,
        status=FactStatus.UNKNOWN,
        confidence=0.0,
    )

    assert (
        RelationshipHypothesisAdapter().from_fact(
            fact,
        )
        == ()
    )


def test_relationship_fact_builder_returns_unknown_without_evidence() -> None:
    fact = build_relationship_fact(())

    assert fact.kind is FactKind.RELATIONSHIP_STATUS

    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None


def test_matching_explicit_relationship_evidence_combines_confidence() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.MARRIED,
                confidence=0.8,
            ),
            build_explicit_evidence(
                RelationshipStatus.MARRIED,
                confidence=0.6,
            ),
        )
    )

    assert fact.status is FactStatus.SUPPORTED

    assert fact.value == RelationshipStatus.MARRIED.value

    assert fact.confidence == 0.92


def test_plain_ring_produces_ambiguous_hypothesis() -> None:
    adapter = RelationshipHypothesisAdapter()

    observations = adapter.from_signals(
        (
            RelationshipSignal(
                kind=RelationshipSignalKind.RING_EMOJI,
                raw_value="💍",
                weight=0.45,
            ),
        )
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    assert result.status is HypothesisStatus.AMBIGUOUS

    assert result.best_value == RelationshipStatus.UNKNOWN.value

    assert result.confidence == 0.45


def test_explicit_single_plus_ring_is_not_conflicted() -> None:
    fact = build_relationship_fact(
        (
            build_explicit_evidence(
                RelationshipStatus.SINGLE,
            ),
        )
    )

    observations = RelationshipHypothesisAdapter().combine(
        fact=fact,
        signals=(
            RelationshipSignal(
                kind=RelationshipSignalKind.RING_EMOJI,
                raw_value="💍",
                weight=0.45,
            ),
        ),
    )

    result = build_service().evaluate(
        HypothesisKind.RELATIONSHIP_STATUS,
        observations,
    )

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED

    assert result.best_value == RelationshipStatus.SINGLE.value
