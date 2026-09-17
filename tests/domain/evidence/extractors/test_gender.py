"""Tests for explicit self-declared gender extraction."""

import pytest

from veyra.domain.evidence import (
    BioDeclaredGenderExtractor,
    DeclaredGender,
    EvidenceSource,
    FactCardinality,
    FactKind,
    fact_cardinality_for,
)
from veyra.domain.intelligence import EvidenceNature, EvidenceStrength


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        ("she/her | engineer", DeclaredGender.FEMALE),
        ("She • Her | تهران", DeclaredGender.FEMALE),
        ("I'm a woman | developer", DeclaredGender.FEMALE),
        ("من یک زن هستم | برنامه نویس", DeclaredGender.FEMALE),
        ("خانم | Software Engineer", DeclaredGender.FEMALE),
        ("بانو • تهران", DeclaredGender.FEMALE),
        ("دختر | تهران", DeclaredGender.FEMALE),
        ("he/him | engineer", DeclaredGender.MALE),
        ("I am a man | developer", DeclaredGender.MALE),
        ("من یک مرد هستم | مهندس", DeclaredGender.MALE),
        ("آقا | تهران", DeclaredGender.MALE),
        ("پسر | تهران", DeclaredGender.MALE),
    ),
)
def test_extracts_explicit_declared_gender(
    bio: str,
    expected: DeclaredGender,
) -> None:
    evidence = BioDeclaredGenderExtractor().extract(
        bio,
    )

    assert len(evidence) == 1

    item = evidence[0]

    assert item.normalized_value == expected.value
    assert item.source is EvidenceSource.BIO
    assert item.confidence == 0.99
    assert item.extractor == "bio_declared_gender_explicit"
    assert item.nature is EvidenceNature.EXPLICIT
    assert item.strength is EvidenceStrength.VERY_STRONG


@pytest.mark.parametrize(
    "bio",
    (
        "",
        " ",
        "Sara | engineer",
        "دختر پاییز",
        "girl dad",
        "women's rights",
        "حقوق زنان",
        "👩🏻‍💻 | developer",
        "💄✨",
    ),
)
def test_ignores_contextual_or_proxy_gender_cues(
    bio: str,
) -> None:
    assert (
        BioDeclaredGenderExtractor().extract(
            bio,
        )
        == ()
    )


def test_conflicting_explicit_gender_evidence_is_preserved() -> None:
    evidence = BioDeclaredGenderExtractor().extract(
        "she/her | he/him",
    )

    assert tuple(item.normalized_value for item in evidence) == (
        DeclaredGender.FEMALE.value,
        DeclaredGender.MALE.value,
    )


def test_declared_gender_fact_is_scalar() -> None:
    assert (
        fact_cardinality_for(
            FactKind.DECLARED_GENDER,
        )
        is FactCardinality.SINGLE
    )
