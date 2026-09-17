"""Additional Fact entity tests for multi-value semantics."""

import pytest

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    Fact,
    FactCardinality,
    FactKind,
    FactStatus,
)


def item(value: str) -> Evidence:
    """Create one evidence item."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value=value,
        normalized_value=value,
        confidence=0.9,
    )


def test_supported_multi_value_fact_requires_values() -> None:
    with pytest.raises(
        ValueError,
        match="must contain values",
    ):
        Fact(
            kind=FactKind.EDUCATION,
            status=FactStatus.SUPPORTED,
            confidence=0.9,
            evidence=(item("bachelor:cs"),),
        )


def test_supported_multi_value_fact_rejects_scalar_value() -> None:
    with pytest.raises(
        ValueError,
        match="must not have a scalar value",
    ):
        Fact(
            kind=FactKind.EDUCATION,
            status=FactStatus.SUPPORTED,
            confidence=0.9,
            value="bachelor:cs",
            values=("bachelor:cs",),
            evidence=(item("bachelor:cs"),),
        )


def test_supported_multi_value_fact_rejects_duplicate_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        Fact(
            kind=FactKind.INSTITUTION,
            status=FactStatus.SUPPORTED,
            confidence=0.9,
            values=("mit", "mit"),
            evidence=(item("mit"),),
        )


def test_supported_scalar_fact_rejects_values_collection() -> None:
    with pytest.raises(
        ValueError,
        match="must not have multiple values",
    ):
        Fact(
            kind=FactKind.OCCUPATION,
            status=FactStatus.SUPPORTED,
            confidence=0.9,
            value="engineer",
            values=("engineer",),
            evidence=(item("engineer"),),
        )


def test_multi_value_fact_exposes_cardinality() -> None:
    fact = Fact(
        kind=FactKind.INSTITUTION,
        status=FactStatus.SUPPORTED,
        confidence=0.9,
        values=("mit",),
        evidence=(item("mit"),),
    )

    assert fact.cardinality is FactCardinality.MULTIPLE
