"""Tests for explicit education degree and field extraction."""

import pytest

from veyra.domain.evidence import (
    BioEducationExtractor,
    EducationCredential,
    EducationLevel,
    EvidenceSource,
)
from veyra.domain.intelligence import EvidenceNature, EvidenceStrength


def values(
    text: str,
) -> set[str]:
    """Return normalized education values."""

    return {
        str(item.normalized_value)
        for item in BioEducationExtractor().extract(
            text,
        )
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("BSc Computer Science", {"bachelor:computer science"}),
        ("B.Sc. Computer Science", {"bachelor:computer science"}),
        ("BS in Computer Science", {"bachelor:computer science"}),
        ("Bachelor in Computer Science", {"bachelor:computer science"}),
        ("Bachelor's in Computer Science", {"bachelor:computer science"}),
        ("Bachelor of Computer Engineering", {"bachelor:computer engineering"}),
        ("MSc Data Science", {"master:data science"}),
        ("M.S. in Data Science", {"master:data science"}),
        ("Master in Artificial Intelligence", {"master:artificial intelligence"}),
        ("Master's of Data Science", {"master:data science"}),
        ("PhD in Artificial Intelligence", {"doctorate:artificial intelligence"}),
        ("Ph.D. Computer Science", {"doctorate:computer science"}),
        ("Doctorate in Physics", {"doctorate:physics"}),
        ("Associate Degree in Design", {"associate:design"}),
    ),
)
def test_extracts_explicit_english_degree_and_field(
    text: str,
    expected: set[str],
) -> None:
    assert values(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("کارشناسی مهندسی نرم افزار", {"bachelor:مهندسی نرم افزار"}),
        ("لیسانس علوم کامپیوتر", {"bachelor:علوم کامپیوتر"}),
        ("کارشناسی رشته مهندسی کامپیوتر", {"bachelor:مهندسی کامپیوتر"}),
        ("کارشناسی ارشد علوم داده", {"master:علوم داده"}),
        ("فوق لیسانس هوش مصنوعی", {"master:هوش مصنوعی"}),
        ("دکتری هوش مصنوعی", {"doctorate:هوش مصنوعی"}),
        ("دکترا فیزیک", {"doctorate:فیزیک"}),
        ("کاردانی طراحی گرافیک", {"associate:طراحی گرافیک"}),
        ("فوق دیپلم کامپیوتر", {"associate:کامپیوتر"}),
    ),
)
def test_extracts_explicit_persian_degree_and_field(
    text: str,
    expected: set[str],
) -> None:
    assert values(text) == expected


def test_half_space_is_normalized_in_persian_field() -> None:
    assert values(
        "کارشناسی مهندسی نرم‌افزار",
    ) == {
        "bachelor:مهندسی نرم افزار",
    }


def test_english_institution_suffix_is_not_part_of_field() -> None:
    assert values(
        "BSc Computer Science at MIT",
    ) == {
        "bachelor:computer science",
    }


def test_persian_institution_suffix_is_not_part_of_field() -> None:
    assert values(
        "کارشناسی مهندسی نرم افزار در دانشگاه تهران",
    ) == {
        "bachelor:مهندسی نرم افزار",
    }


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "Computer Science",
        "Data Science",
        "Software Engineer",
        "Student at MIT",
        "Graduate of Tehran University",
        "Studying at Sharif University",
        "دانشجوی دانشگاه تهران",
        "مهندسی نرم افزار",
        "علوم داده",
        "فارغ التحصیل دانشگاه تهران",
    ),
)
def test_non_degree_text_does_not_create_education_evidence(
    text: str,
) -> None:
    assert values(text) == set()


def test_multiple_explicit_credentials_are_retained() -> None:
    assert values(
        "BSc Computer Science | MSc Data Science",
    ) == {
        "bachelor:computer science",
        "master:data science",
    }


def test_duplicate_credentials_are_deduplicated() -> None:
    evidence = BioEducationExtractor().extract(
        "BSc Computer Science | BSc Computer Science",
    )

    assert len(evidence) == 1
    assert evidence[0].normalized_value == "bachelor:computer science"


def test_education_evidence_uses_bio_source() -> None:
    item = BioEducationExtractor().extract(
        "BSc Computer Science",
    )[0]

    assert item.source is EvidenceSource.BIO


def test_education_evidence_is_explicit_and_very_strong() -> None:
    item = BioEducationExtractor().extract(
        "MSc Data Science",
    )[0]

    assert item.nature is EvidenceNature.EXPLICIT
    assert item.strength is EvidenceStrength.VERY_STRONG


def test_education_evidence_uses_expected_extractor_name() -> None:
    item = BioEducationExtractor().extract(
        "PhD in AI",
    )[0]

    assert item.extractor == "bio_education_explicit"


def test_default_education_confidence() -> None:
    item = BioEducationExtractor().extract(
        "BSc Computer Science",
    )[0]

    assert item.confidence == 0.97


def test_education_credential_value_with_field() -> None:
    credential = EducationCredential(
        level=EducationLevel.MASTER,
        field=" Data Science ",
    )

    assert credential.field == "data science"
    assert credential.value == "master:data science"


def test_education_credential_normalizes_half_space() -> None:
    credential = EducationCredential(
        level=EducationLevel.BACHELOR,
        field="مهندسی نرم‌افزار",
    )

    assert credential.field == "مهندسی نرم افزار"
    assert credential.value == "bachelor:مهندسی نرم افزار"


@pytest.mark.parametrize(
    "confidence",
    (
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_education_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        BioEducationExtractor(
            confidence=confidence,
        )
