"""Tests for explicit education-institution evidence extraction."""

import pytest

from veyra.domain.evidence import (
    BioInstitutionExtractor,
    EvidenceSource,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
)


def values(
    text: str,
) -> set[str]:
    """Return normalized institution values extracted from biography text."""

    return {
        str(item.normalized_value)
        for item in BioInstitutionExtractor().extract(
            text,
        )
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        (
            "Student at Tehran University",
            {"tehran university"},
        ),
        (
            "Undergraduate at University of Tehran",
            {"university of tehran"},
        ),
        (
            "Postgraduate at Sharif University",
            {"sharif university"},
        ),
        (
            "PhD Student at MIT",
            {"mit"},
        ),
        (
            "Doctoral Student at Oxford University",
            {"oxford university"},
        ),
        (
            "Studying at University of Tehran",
            {"university of tehran"},
        ),
        (
            "Graduate of University of Tehran",
            {"university of tehran"},
        ),
        (
            "Alumni of Sharif University",
            {"sharif university"},
        ),
        (
            "Educated at Cambridge University",
            {"cambridge university"},
        ),
    ),
)
def test_extracts_explicit_english_institution(
    text: str,
    expected: set[str],
) -> None:
    assert (
        values(
            text,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        (
            "دانشجوی دانشگاه تهران",
            {"دانشگاه تهران"},
        ),
        (
            "دانشجو در دانشگاه شریف",
            {"دانشگاه شریف"},
        ),
        (
            "در حال تحصیل در دانشگاه تهران",
            {"دانشگاه تهران"},
        ),
        (
            "مشغول به تحصیل در دانشگاه علم و صنعت",
            {"دانشگاه علم و صنعت"},
        ),
        (
            "فارغ التحصیل دانشگاه تهران",
            {"دانشگاه تهران"},
        ),
        (
            "فارغ‌التحصیل دانشگاه شریف",
            {"دانشگاه شریف"},
        ),
        (
            "تحصیل در دانشگاه امیرکبیر",
            {"دانشگاه امیرکبیر"},
        ),
    ),
)
def test_extracts_explicit_persian_institution(
    text: str,
    expected: set[str],
) -> None:
    assert (
        values(
            text,
        )
        == expected
    )


def test_persian_half_space_is_normalized() -> None:
    assert values(
        "فارغ‌التحصیل دانشگاه تهران",
    ) == {
        "دانشگاه تهران",
    }


def test_leading_english_article_is_removed() -> None:
    assert values(
        "Student at The University of Manchester",
    ) == {
        "university of manchester",
    }


def test_institution_evidence_retains_original_bio() -> None:
    text = "Student at Tehran University"

    evidence = BioInstitutionExtractor().extract(
        text,
    )

    assert len(evidence) == 1
    assert evidence[0].raw_value == text


def test_institution_evidence_uses_bio_source() -> None:
    evidence = BioInstitutionExtractor().extract(
        "Student at Tehran University",
    )

    assert len(evidence) == 1
    assert evidence[0].source is EvidenceSource.BIO


def test_institution_evidence_is_explicit_and_very_strong() -> None:
    item = BioInstitutionExtractor().extract(
        "Student at Tehran University",
    )[0]

    assert item.nature is EvidenceNature.EXPLICIT
    assert item.strength is EvidenceStrength.VERY_STRONG


def test_institution_evidence_uses_expected_extractor_name() -> None:
    item = BioInstitutionExtractor().extract(
        "Student at Tehran University",
    )[0]

    assert item.extractor == "bio_institution_explicit"


def test_default_institution_confidence() -> None:
    item = BioInstitutionExtractor().extract(
        "Student at Tehran University",
    )[0]

    assert item.confidence == 0.97


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "Tehran University",
        "MIT",
        "University of Tehran",
        "I visited Tehran University",
        "Conference at Tehran University",
        "Coffee near Tehran University",
        "دانشگاه تهران",
        "بازدید از دانشگاه تهران",
    ),
)
def test_plain_or_contextual_mention_does_not_create_institution_fact(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


@pytest.mark.parametrize(
    "text",
    (
        "Software Engineer at Tehran University",
        "Developer at Sharif University",
        "Works at University of Tehran",
        "Research Engineer at Oxford University",
        "مهندس نرم افزار در دانشگاه تهران",
        "در دانشگاه تهران کار می کنم",
        "در دانشگاه تهران کار می‌کنم",
    ),
)
def test_employment_affiliation_does_not_create_education_institution(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


@pytest.mark.parametrize(
    "text",
    (
        "Based in Tehran",
        "Living in London",
        "Student in Tehran",
        "دانشجو در تهران",
        "ساکن تهران",
    ),
)
def test_location_only_context_does_not_create_institution(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


@pytest.mark.parametrize(
    "text",
    (
        "Student at https://example.com",
        "Graduate of www.example.com",
        "Student at @university",
    ),
)
def test_url_or_social_handle_is_rejected(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


def test_pipe_stops_institution_capture() -> None:
    assert values(
        "Student at Tehran University | Photographer",
    ) == {
        "tehran university",
    }


def test_english_comma_stops_institution_capture() -> None:
    assert values(
        "Graduate of Sharif University, Tehran",
    ) == {
        "sharif university",
    }


def test_persian_comma_stops_institution_capture() -> None:
    assert values(
        "دانشجوی دانشگاه تهران، برنامه نویس",
    ) == {
        "دانشگاه تهران",
    }


def test_multiple_explicit_institutions_are_retained() -> None:
    assert values(
        "Graduate of Sharif University | Student at MIT",
    ) == {
        "sharif university",
        "mit",
    }


def test_duplicate_institution_claim_is_deduplicated() -> None:
    evidence = BioInstitutionExtractor().extract(
        "Graduate of MIT | Student at MIT",
    )

    assert len(evidence) == 1
    assert evidence[0].normalized_value == "mit"


@pytest.mark.parametrize(
    "confidence",
    (
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        BioInstitutionExtractor(
            confidence=confidence,
        )
