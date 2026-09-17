"""Tests for intelligence taxonomy enumerations."""

from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    HypothesisKind,
    RelationshipStatus,
)


def test_evidence_nature_has_expected_values() -> None:
    assert EvidenceNature.EXPLICIT.value == "explicit"
    assert EvidenceNature.OBSERVED.value == "observed"
    assert EvidenceNature.CONTEXTUAL.value == "contextual"
    assert EvidenceNature.DERIVED.value == "derived"
    assert EvidenceNature.AMBIGUOUS.value == "ambiguous"


def test_evidence_strength_has_expected_labels() -> None:
    assert EvidenceStrength.WEAK.value == "weak"
    assert EvidenceStrength.MODERATE.value == "moderate"
    assert EvidenceStrength.STRONG.value == "strong"
    assert EvidenceStrength.VERY_STRONG.value == "very_strong"


def test_relationship_status_supports_expected_values() -> None:
    assert RelationshipStatus.SINGLE.value == "single"
    assert RelationshipStatus.MARRIED.value == "married"
    assert RelationshipStatus.ENGAGED.value == "engaged"

    assert RelationshipStatus.IN_RELATIONSHIP.value == "in_relationship"

    assert RelationshipStatus.DIVORCED.value == "divorced"
    assert RelationshipStatus.WIDOWED.value == "widowed"
    assert RelationshipStatus.UNKNOWN.value == "unknown"


def test_relationship_status_is_supported_as_hypothesis() -> None:
    assert HypothesisKind.RELATIONSHIP_STATUS.value == "relationship_status"
