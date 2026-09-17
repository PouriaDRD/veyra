"""Tests for confidence calculations."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    combine_confidences,
    conflict_confidence,
)


def build_evidence(
    confidence: float,
) -> Evidence:
    """Create generic evidence."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value="2000",
        normalized_value=2000,
        confidence=confidence,
    )


def test_combine_confidences_returns_zero_without_evidence() -> None:
    assert combine_confidences(()) == 0.0


def test_combine_confidences_increases_support() -> None:
    confidence = combine_confidences(
        (
            build_evidence(0.8),
            build_evidence(0.6),
        )
    )

    assert confidence == 0.92


def test_conflict_confidence_uses_two_strongest_items() -> None:
    confidence = conflict_confidence(
        (
            build_evidence(0.95),
            build_evidence(0.8),
            build_evidence(0.4),
        )
    )

    assert confidence == 0.8
