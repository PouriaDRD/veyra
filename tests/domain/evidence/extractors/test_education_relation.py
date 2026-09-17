"""Tests for education-to-institution relationship extraction."""

import pytest

from veyra.domain.evidence import (
    BioEducationInstitutionRelationExtractor,
    EducationInstitutionRelation,
    EvidenceSource,
)
from veyra.domain.intelligence import EvidenceNature, EvidenceStrength


@pytest.fixture
def extractor() -> BioEducationInstitutionRelationExtractor:
    return BioEducationInstitutionRelationExtractor()


@pytest.mark.parametrize(
    ("bio", "education", "institution"),
    [
        ("BSc Computer Science at MIT", "bachelor:computer science", "mit"),
        (
            "MSc Data Science from Stanford University",
            "master:data science",
            "stanford university",
        ),
        ("PhD at MIT", "doctorate", "mit"),
        (
            "MBA from Harvard University",
            "master:business administration",
            "harvard university",
        ),
        (
            "کارشناسی مهندسی نرم افزار در دانشگاه تهران",
            "bachelor:مهندسی نرم افزار",
            "دانشگاه تهران",
        ),
        (
            "کارشناسی ارشد علوم داده از دانشگاه شریف",
            "master:علوم داده",
            "دانشگاه شریف",
        ),
        ("دکتری در دانشگاه تهران", "doctorate", "دانشگاه تهران"),
    ],
)
def test_explicit_same_segment_relation_is_extracted(
    extractor: BioEducationInstitutionRelationExtractor,
    bio: str,
    education: str,
    institution: str,
) -> None:
    relations = extractor.extract(bio)
    assert len(relations) == 1

    relation = relations[0]
    assert relation.education == education
    assert relation.institution == institution
    assert relation.confidence == 0.97
    assert relation.source is EvidenceSource.BIO
    assert relation.nature is EvidenceNature.EXPLICIT
    assert relation.strength is EvidenceStrength.VERY_STRONG


def test_independent_segments_are_not_cross_linked(
    extractor: BioEducationInstitutionRelationExtractor,
) -> None:
    assert extractor.extract("BSc Computer Science | Student at MIT") == ()


def test_multiple_independent_pairs_are_preserved(
    extractor: BioEducationInstitutionRelationExtractor,
) -> None:
    relations = extractor.extract(
        "BSc Computer Science at MIT | MSc Data Science at Stanford University"
    )
    assert tuple((item.education, item.institution) for item in relations) == (
        ("bachelor:computer science", "mit"),
        ("master:data science", "stanford university"),
    )


def test_persian_multiple_independent_pairs_are_preserved(
    extractor: BioEducationInstitutionRelationExtractor,
) -> None:
    relations = extractor.extract(
        "کارشناسی مهندسی نرم افزار در دانشگاه تهران | کارشناسی ارشد علوم داده در دانشگاه شریف"
    )
    assert tuple((item.education, item.institution) for item in relations) == (
        ("bachelor:مهندسی نرم افزار", "دانشگاه تهران"),
        ("master:علوم داده", "دانشگاه شریف"),
    )


@pytest.mark.parametrize(
    "bio",
    [
        "Student at MIT",
        "BSc Computer Science",
        "MIT",
        "Software Engineer at Tehran University",
        "BSc Computer Science\nStudent at MIT",
    ],
)
def test_unpaired_or_unrelated_segments_do_not_create_relation(
    extractor: BioEducationInstitutionRelationExtractor,
    bio: str,
) -> None:
    assert extractor.extract(bio) == ()


def test_duplicate_pair_is_deduplicated(
    extractor: BioEducationInstitutionRelationExtractor,
) -> None:
    relations = extractor.extract("PhD at MIT | PhD at MIT")
    assert len(relations) == 1
    assert relations[0].education == "doctorate"
    assert relations[0].institution == "mit"


def test_empty_text_returns_no_relations(
    extractor: BioEducationInstitutionRelationExtractor,
) -> None:
    assert extractor.extract("") == ()


def test_relation_entity_normalizes_values() -> None:
    relation = EducationInstitutionRelation(
        education="  MASTER:Data Science  ",
        institution="  Stanford University  ",
        raw_value="  MSc Data Science at Stanford University  ",
        confidence=0.9,
    )
    assert relation.education == "master:data science"
    assert relation.institution == "stanford university"
    assert relation.raw_value == "MSc Data Science at Stanford University"


def test_relation_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        EducationInstitutionRelation(
            education="doctorate",
            institution="mit",
            raw_value="PhD at MIT",
            confidence=1.1,
        )


@pytest.mark.parametrize(
    ("education", "institution", "raw_value", "message"),
    [
        ("", "mit", "PhD at MIT", "education must not be empty"),
        ("doctorate", "", "PhD at MIT", "institution must not be empty"),
        ("doctorate", "mit", " ", "raw_value must not be empty"),
    ],
)
def test_relation_rejects_empty_required_values(
    education: str,
    institution: str,
    raw_value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        EducationInstitutionRelation(
            education=education,
            institution=institution,
            raw_value=raw_value,
            confidence=0.97,
        )
