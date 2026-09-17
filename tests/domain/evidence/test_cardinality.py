"""Tests for fact cardinality policy."""

from veyra.domain.evidence import (
    FactCardinality,
    FactKind,
    fact_cardinality_for,
)


def test_education_is_multi_value() -> None:
    assert fact_cardinality_for(FactKind.EDUCATION) is FactCardinality.MULTIPLE


def test_institution_is_multi_value() -> None:
    assert fact_cardinality_for(FactKind.INSTITUTION) is FactCardinality.MULTIPLE


def test_birth_year_remains_scalar() -> None:
    assert fact_cardinality_for(FactKind.BIRTH_YEAR) is FactCardinality.SINGLE


def test_occupation_remains_scalar() -> None:
    assert fact_cardinality_for(FactKind.OCCUPATION) is FactCardinality.SINGLE
