"""Tests for confidence calculations."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    combine_confidences,
    conflict_confidence,
)


def build_evidence(
    value: int,
    confidence: float,
) -> Evidence:
    """Create generic evidence."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value=str(value),
        normalized_value=value,
        confidence=confidence,
    )


def test_combine_confidences_returns_zero_without_evidence() -> None:
    assert combine_confidences(()) == 0.0


def test_combine_confidences_increases_support() -> None:
    confidence = combine_confidences(
        (
            build_evidence(
                2000,
                0.8,
            ),
            build_evidence(
                2000,
                0.6,
            ),
        )
    )

    assert confidence == 0.92


def test_conflict_confidence_returns_zero_without_competing_values() -> None:
    confidence = conflict_confidence(
        (
            build_evidence(
                2000,
                0.95,
            ),
            build_evidence(
                2000,
                0.8,
            ),
        )
    )

    assert confidence == 0.0


def test_conflict_confidence_uses_weaker_competing_interpretation() -> None:
    confidence = conflict_confidence(
        (
            build_evidence(
                1999,
                0.8,
            ),
            build_evidence(
                2001,
                0.95,
            ),
        )
    )

    assert confidence == 0.8


def test_matching_evidence_does_not_overstate_conflict() -> None:
    confidence = conflict_confidence(
        (
            build_evidence(
                2000,
                0.95,
            ),
            build_evidence(
                2000,
                0.9,
            ),
            build_evidence(
                2001,
                0.4,
            ),
        )
    )

    assert confidence == 0.4


def test_repeated_support_can_strengthen_competing_interpretation() -> None:
    confidence = conflict_confidence(
        (
            build_evidence(
                2000,
                0.9,
            ),
            build_evidence(
                2001,
                0.5,
            ),
            build_evidence(
                2001,
                0.5,
            ),
        )
    )

    assert confidence == 0.75
