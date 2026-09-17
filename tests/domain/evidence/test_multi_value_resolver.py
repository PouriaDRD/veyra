"""Tests for multi-value fact resolution."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    FactCardinality,
    FactKind,
    FactResolver,
    FactStatus,
)


def evidence(
    value: str,
    *,
    confidence: float = 0.9,
    ambiguous: bool = False,
) -> Evidence:
    """Create BIO evidence for resolver tests."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value=value,
        normalized_value=value,
        confidence=confidence,
        is_ambiguous=ambiguous,
    )


def test_distinct_education_values_are_supported_together() -> None:
    fact = FactResolver().resolve(
        FactKind.EDUCATION,
        (
            evidence("bachelor:computer science", confidence=0.97),
            evidence("master:data science", confidence=0.96),
        ),
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.cardinality is FactCardinality.MULTIPLE
    assert fact.value is None
    assert fact.values == (
        "bachelor:computer science",
        "master:data science",
    )
    assert fact.confidence == 0.96


def test_distinct_institutions_are_supported_together() -> None:
    fact = FactResolver().resolve(
        FactKind.INSTITUTION,
        (
            evidence("sharif university", confidence=0.97),
            evidence("mit", confidence=0.95),
        ),
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.values == (
        "mit",
        "sharif university",
    )


def test_duplicate_multi_value_combines_confidence() -> None:
    fact = FactResolver().resolve(
        FactKind.INSTITUTION,
        (
            evidence("mit", confidence=0.8),
            evidence("mit", confidence=0.9),
        ),
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.values == ("mit",)
    assert fact.confidence == 0.98


def test_multi_value_confidence_is_weakest_supported_value() -> None:
    fact = FactResolver().resolve(
        FactKind.EDUCATION,
        (
            evidence("bachelor:computer science", confidence=0.99),
            evidence("master:data science", confidence=0.72),
        ),
    )

    assert fact.confidence == 0.72


def test_matching_ambiguous_evidence_strengthens_definitive_multi_value() -> None:
    fact = FactResolver().resolve(
        FactKind.INSTITUTION,
        (
            evidence("mit", confidence=0.8),
            evidence("mit", confidence=0.5, ambiguous=True),
            evidence("stanford", confidence=0.9),
        ),
    )

    assert fact.values == (
        "mit",
        "stanford",
    )
    assert fact.confidence == 0.9


def test_unmatched_ambiguous_value_does_not_join_multi_value_fact() -> None:
    fact = FactResolver().resolve(
        FactKind.INSTITUTION,
        (
            evidence("mit", confidence=0.9),
            evidence("stanford", confidence=0.4, ambiguous=True),
        ),
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.values == ("mit",)
    assert tuple(item.normalized_value for item in fact.evidence) == ("mit",)


def test_ambiguous_only_distinct_values_remain_conflicted() -> None:
    fact = FactResolver().resolve(
        FactKind.INSTITUTION,
        (
            evidence("mit", confidence=0.4, ambiguous=True),
            evidence("stanford", confidence=0.4, ambiguous=True),
        ),
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None
    assert fact.values == ()


def test_scalar_fact_still_conflicts_on_distinct_values() -> None:
    fact = FactResolver().resolve(
        FactKind.OCCUPATION,
        (
            evidence("software engineer"),
            evidence("photographer"),
        ),
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None
    assert fact.values == ()
