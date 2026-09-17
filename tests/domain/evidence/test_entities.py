"""Tests for evidence domain entities."""

import pytest

from veyra.domain.evidence import (
    ConfidenceLevel,
    Evidence,
    EvidenceSource,
    Fact,
    FactKind,
    FactStatus,
)


def build_birth_year_evidence(
    year: int,
    *,
    confidence: float = 0.9,
) -> Evidence:
    """Create birth-year evidence for tests."""

    return Evidence(
        source=EvidenceSource.USERNAME,
        raw_value=str(year),
        normalized_value=year,
        confidence=confidence,
        extractor="username_birth_year",
    )


def test_evidence_normalizes_raw_value() -> None:
    evidence = Evidence(
        source=EvidenceSource.BIO,
        raw_value="  Tehran  ",
        normalized_value="Tehran",
        confidence=0.8,
    )

    assert evidence.raw_value == "Tehran"


def test_evidence_rejects_invalid_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="confidence must be between 0 and 1",
    ):
        Evidence(
            source=EvidenceSource.BIO,
            raw_value="Tehran",
            normalized_value="Tehran",
            confidence=1.1,
        )


def test_supported_fact_requires_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="supported fact must contain evidence",
    ):
        Fact(
            kind=FactKind.BIRTH_YEAR,
            status=FactStatus.SUPPORTED,
            value=2000,
            confidence=0.9,
        )


def test_supported_fact_exposes_confidence_level() -> None:
    evidence = build_birth_year_evidence(
        2000,
    )

    fact = Fact(
        kind=FactKind.BIRTH_YEAR,
        status=FactStatus.SUPPORTED,
        value=2000,
        confidence=0.9,
        evidence=(evidence,),
    )

    assert fact.confidence_level is ConfidenceLevel.VERY_HIGH


def test_conflicted_fact_requires_multiple_evidence_items() -> None:
    evidence = build_birth_year_evidence(
        2000,
    )

    with pytest.raises(
        ValueError,
        match="at least two evidence",
    ):
        Fact(
            kind=FactKind.BIRTH_YEAR,
            status=FactStatus.CONFLICTED,
            confidence=0.4,
            evidence=(evidence,),
        )


def test_conflicted_fact_has_no_resolved_value() -> None:
    first = build_birth_year_evidence(
        1999,
    )

    second = Evidence(
        source=EvidenceSource.BIO,
        raw_value="2001",
        normalized_value=2001,
        confidence=0.95,
        extractor="bio_birth_year",
    )

    fact = Fact(
        kind=FactKind.BIRTH_YEAR,
        status=FactStatus.CONFLICTED,
        confidence=0.3,
        evidence=(
            first,
            second,
        ),
    )

    assert fact.value is None
    assert fact.status is FactStatus.CONFLICTED


def test_unknown_fact_has_zero_confidence() -> None:
    fact = Fact(
        kind=FactKind.LOCATION,
        status=FactStatus.UNKNOWN,
        confidence=0,
    )

    assert fact.value is None
    assert fact.evidence == ()
