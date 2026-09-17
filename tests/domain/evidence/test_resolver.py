"""Tests for fact resolution."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    FactKind,
    FactResolver,
    FactStatus,
)


def test_resolver_returns_unknown_without_evidence() -> None:
    fact = FactResolver().resolve(
        FactKind.BIRTH_YEAR,
        (),
    )

    assert fact.status is FactStatus.UNKNOWN
    assert fact.value is None
    assert fact.confidence == 0


def test_resolver_combines_matching_evidence() -> None:
    evidence = (
        Evidence(
            source=EvidenceSource.USERNAME,
            raw_value="2000",
            normalized_value=2000,
            confidence=0.8,
        ),
        Evidence(
            source=EvidenceSource.BIO,
            raw_value="born 2000",
            normalized_value=2000,
            confidence=0.9,
        ),
    )

    fact = FactResolver().resolve(
        FactKind.BIRTH_YEAR,
        evidence,
    )

    assert fact.status is FactStatus.SUPPORTED
    assert fact.value == 2000
    assert fact.confidence == 0.98


def test_resolver_marks_conflicting_values() -> None:
    evidence = (
        Evidence(
            source=EvidenceSource.USERNAME,
            raw_value="1999",
            normalized_value=1999,
            confidence=0.8,
        ),
        Evidence(
            source=EvidenceSource.BIO,
            raw_value="born 2001",
            normalized_value=2001,
            confidence=0.95,
        ),
    )

    fact = FactResolver().resolve(
        FactKind.BIRTH_YEAR,
        evidence,
    )

    assert fact.status is FactStatus.CONFLICTED
    assert fact.value is None
    assert fact.confidence == 0.8
