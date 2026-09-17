"""Tests for multilingual relationship-status extraction."""

import pytest

from veyra.domain.evidence.extractors import (
    BioRelationshipStatusExtractor,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    RelationshipStatus,
)


@pytest.fixture
def extractor() -> BioRelationshipStatusExtractor:
    """Create relationship extractor."""

    return BioRelationshipStatusExtractor()


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        # --------------------------------------------------
        # English
        # --------------------------------------------------
        (
            "Married",
            RelationshipStatus.MARRIED,
        ),
        (
            "MARRIED",
            RelationshipStatus.MARRIED,
        ),
        (
            "married 💍",
            RelationshipStatus.MARRIED,
        ),
        (
            "Single",
            RelationshipStatus.SINGLE,
        ),
        (
            "SINGLE",
            RelationshipStatus.SINGLE,
        ),
        (
            "Engaged",
            RelationshipStatus.ENGAGED,
        ),
        (
            "ENGAGED 💍",
            RelationshipStatus.ENGAGED,
        ),
        (
            "In a relationship",
            RelationshipStatus.IN_RELATIONSHIP,
        ),
        (
            "in relationship",
            RelationshipStatus.IN_RELATIONSHIP,
        ),
        (
            "Divorced",
            RelationshipStatus.DIVORCED,
        ),
        (
            "Widowed",
            RelationshipStatus.WIDOWED,
        ),
        (
            "Widow",
            RelationshipStatus.WIDOWED,
        ),
        (
            "Widower",
            RelationshipStatus.WIDOWED,
        ),
        # --------------------------------------------------
        # Persian
        # --------------------------------------------------
        (
            "متاهل",
            RelationshipStatus.MARRIED,
        ),
        (
            "متأهل",
            RelationshipStatus.MARRIED,
        ),
        (
            "متاهل 💍",
            RelationshipStatus.MARRIED,
        ),
        (
            "مجرد",
            RelationshipStatus.SINGLE,
        ),
        (
            "نامزد",
            RelationshipStatus.ENGAGED,
        ),
        (
            "نامزد 💍",
            RelationshipStatus.ENGAGED,
        ),
        (
            "در رابطه",
            RelationshipStatus.IN_RELATIONSHIP,
        ),
        (
            "مطلقه",
            RelationshipStatus.DIVORCED,
        ),
        (
            "طلاق گرفته",
            RelationshipStatus.DIVORCED,
        ),
        (
            "بیوه",
            RelationshipStatus.WIDOWED,
        ),
        # --------------------------------------------------
        # Mixed language
        # --------------------------------------------------
        (
            "Tehran | Married 💍",
            RelationshipStatus.MARRIED,
        ),
        (
            "Developer | مجرد",
            RelationshipStatus.SINGLE,
        ),
        (
            "نامزد | Software Engineer",
            RelationshipStatus.ENGAGED,
        ),
        (
            "Photographer | in a relationship",
            RelationshipStatus.IN_RELATIONSHIP,
        ),
        (
            "تهران | divorced",
            RelationshipStatus.DIVORCED,
        ),
    ),
)
def test_explicit_relationship_statuses_are_detected(
    extractor: BioRelationshipStatusExtractor,
    bio: str,
    expected: RelationshipStatus,
) -> None:
    evidence = extractor.extract(
        bio,
    )

    assert len(evidence) == 1

    item = evidence[0]

    assert item.normalized_value == expected.value

    assert item.nature is EvidenceNature.EXPLICIT

    assert item.strength is EvidenceStrength.VERY_STRONG

    assert item.confidence == 0.98


@pytest.mark.parametrize(
    "bio",
    (
        # --------------------------------------------------
        # Empty / unrelated
        # --------------------------------------------------
        "",
        " ",
        "Developer",
        "Photographer",
        "Tehran",
        "تهران",
        "Python Django",
        "Coffee lover",
        # --------------------------------------------------
        # Emoji alone
        # --------------------------------------------------
        "💍",
        "❤️",
        "💍 ❤️",
        "Ali ❤️",
        "Sara 💍",
        "علی ❤️",
        "سارا 💍",
        # --------------------------------------------------
        # English negation
        # --------------------------------------------------
        "not married",
        "NOT MARRIED",
        "never married",
        "not single",
        "not engaged",
        "not in a relationship",
        # --------------------------------------------------
        # Persian negation
        # --------------------------------------------------
        "متاهل نیستم",
        "متأهل نیستم",
        "متاهل نیست",
        "مجرد نیستم",
        "مجرد نیست",
        "نامزد نیستم",
        "نامزد نیست",
        "در رابطه نیستم",
        "در رابطه نیست",
        # --------------------------------------------------
        # Historical statements
        # --------------------------------------------------
        "formerly married",
        "previously married",
        "used to be married",
        "was married",
        "formerly single",
        "previously single",
        "used to be single",
        "قبلا متاهل بودم",
        "قبلاً متاهل بودم",
        "متاهل بودم",
        "قبلا مجرد بودم",
        "قبلاً مجرد بودم",
        "مجرد بودم",
        # --------------------------------------------------
        # Metaphorical marriage
        # --------------------------------------------------
        "married to my work",
        "married to work",
        "married to my job",
        "married to music",
        "married to coffee",
        "married to art",
        "married to coding",
        "married to my career",
        # --------------------------------------------------
        # False-positive single expressions
        # --------------------------------------------------
        "single malt lover",
        "single page application developer",
        "single origin coffee",
        "single player gamer",
        "single thread performance",
        "single file component",
        "single core benchmark",
        "single purpose tool",
        "single source of truth",
        "single room available",
        "single bed room",
    ),
)
def test_non_current_or_non_relationship_phrases_are_ignored(
    extractor: BioRelationshipStatusExtractor,
    bio: str,
) -> None:
    assert (
        extractor.extract(
            bio,
        )
        == ()
    )


def test_multiple_current_explicit_claims_are_preserved_for_conflict_resolution(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("Single | Married")

    values = {item.normalized_value for item in evidence}

    assert values == {
        RelationshipStatus.SINGLE.value,
        RelationshipStatus.MARRIED.value,
    }


def test_mixed_persian_conflicting_claims_are_preserved(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("مجرد | متاهل")

    values = {item.normalized_value for item in evidence}

    assert values == {
        RelationshipStatus.SINGLE.value,
        RelationshipStatus.MARRIED.value,
    }


def test_mixed_language_conflicting_claims_are_preserved(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("مجرد | Married")

    values = {item.normalized_value for item in evidence}

    assert values == {
        RelationshipStatus.SINGLE.value,
        RelationshipStatus.MARRIED.value,
    }


def test_negated_married_does_not_create_single_fact(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("not married")

    assert evidence == ()


def test_negated_single_does_not_create_married_fact(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("not single")

    assert evidence == ()


def test_persian_negated_married_does_not_create_single_fact(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("متاهل نیستم")

    assert evidence == ()


def test_persian_negated_single_does_not_create_married_fact(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("مجرد نیستم")

    assert evidence == ()


def test_explicit_claim_preserves_original_raw_bio(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    bio = "Developer | Married 💍 | Tehran"

    evidence = extractor.extract(
        bio,
    )

    assert len(evidence) == 1
    assert evidence[0].raw_value == bio


def test_duplicate_word_does_not_duplicate_same_status(
    extractor: BioRelationshipStatusExtractor,
) -> None:
    evidence = extractor.extract("Married | married | MARRIED")

    assert len(evidence) == 1

    assert evidence[0].normalized_value == RelationshipStatus.MARRIED.value


@pytest.mark.parametrize(
    "bio",
    (
        "MARRIED💍",
        "married|developer",
        "developer|married",
        "متاهل|برنامه نویس",
        "برنامه نویس|متاهل",
        "مجرد|تهران",
        "نامزد|تهران",
    ),
)
def test_relationship_claims_work_next_to_punctuation(
    extractor: BioRelationshipStatusExtractor,
    bio: str,
) -> None:
    evidence = extractor.extract(
        bio,
    )

    assert evidence


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        (
            "متاهل   ",
            RelationshipStatus.MARRIED,
        ),
        (
            "   مجرد",
            RelationshipStatus.SINGLE,
        ),
        (
            "نامزد   💍",
            RelationshipStatus.ENGAGED,
        ),
        (
            "IN   A   RELATIONSHIP",
            RelationshipStatus.IN_RELATIONSHIP,
        ),
    ),
)
def test_relationship_claims_survive_whitespace_normalization(
    extractor: BioRelationshipStatusExtractor,
    bio: str,
    expected: RelationshipStatus,
) -> None:
    evidence = extractor.extract(
        bio,
    )

    assert len(evidence) == 1

    assert evidence[0].normalized_value == expected.value
