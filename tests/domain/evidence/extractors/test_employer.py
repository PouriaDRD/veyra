"""Tests for explicit current employer evidence extraction."""

import pytest

from veyra.domain.evidence import (
    BioEmployerExtractor,
    EvidenceSource,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
)


def values(
    text: str,
) -> set[str]:
    """Return normalized employer values extracted from biography text."""

    return {
        str(item.normalized_value)
        for item in BioEmployerExtractor().extract(
            text,
        )
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Works at Acme", {"acme"}),
        ("I work at Acme", {"acme"}),
        ("Working at Acme", {"acme"}),
        ("Employed at Acme", {"acme"}),
        ("Employee at Acme", {"acme"}),
        ("Software Engineer at Acme", {"acme"}),
        ("Product Designer at Veyra", {"veyra"}),
        ("مهندس نرم افزار در دیجی کالا", {"دیجی کالا"}),
        ("مهندس نرم‌افزار در دیجی کالا", {"دیجی کالا"}),
        ("طراح محصول در اسنپ", {"اسنپ"}),
        ("در دیجی کالا کار می کنم", {"دیجی کالا"}),
        ("در اسنپ کار می‌کنم", {"اسنپ"}),
    ),
)
def test_extracts_explicit_current_employer(
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
        ("Software Engineer @ Acme", {"acme"}),
        ("Developer@Veyra", {"veyra"}),
        ("مهندس نرم افزار @ دیجی کالا", {"دیجی کالا"}),
        ("مهندس نرم‌افزار@اسنپ", {"اسنپ"}),
    ),
)
def test_extracts_at_shorthand_employer_relation(
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
        ("Software Engineer at Acme Inc.", {"acme"}),
        ("Software Engineer at Acme Ltd", {"acme"}),
        ("Software Engineer at Acme LLC", {"acme"}),
        ("Software Engineer at Acme Corporation", {"acme"}),
        ("Software Engineer at The Acme Company", {"acme"}),
    ),
)
def test_normalizes_common_company_legal_suffixes(
    text: str,
    expected: set[str],
) -> None:
    assert (
        values(
            text,
        )
        == expected
    )


def test_company_prefix_is_removed_from_normalized_value() -> None:
    assert values(
        "مهندس نرم افزار در شرکت دیجی کالا",
    ) == {
        "دیجی کالا",
    }


def test_english_the_prefix_is_removed() -> None:
    assert values(
        "Software Engineer at The Acme",
    ) == {
        "acme",
    }


def test_employer_evidence_retains_original_bio() -> None:
    text = "Software Engineer at Acme"

    evidence = BioEmployerExtractor().extract(
        text,
    )

    assert len(evidence) == 1
    assert evidence[0].raw_value == text


def test_employer_evidence_uses_bio_source() -> None:
    evidence = BioEmployerExtractor().extract(
        "Works at Acme",
    )

    assert len(evidence) == 1
    assert evidence[0].source is EvidenceSource.BIO


def test_employer_evidence_is_explicit_and_very_strong() -> None:
    item = BioEmployerExtractor().extract(
        "Works at Acme",
    )[0]

    assert item.nature is EvidenceNature.EXPLICIT
    assert item.strength is EvidenceStrength.VERY_STRONG


def test_employer_evidence_uses_expected_extractor_name() -> None:
    item = BioEmployerExtractor().extract(
        "Works at Acme",
    )[0]

    assert item.extractor == "bio_employer_explicit"


def test_default_employer_confidence() -> None:
    item = BioEmployerExtractor().extract(
        "Works at Acme",
    )[0]

    assert item.confidence == 0.96


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "Coffee | Tehran | Music",
        "Acme",
        "I like Acme",
        "Acme customer",
        "Follow @acme",
        "@acme",
        "DM @acme",
    ),
)
def test_unrelated_text_does_not_create_employer(
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
        "Software Engineer @ @acme",
        "Developer @ @veyra",
        "مهندس نرم افزار @ @digikala",
    ),
)
def test_social_handle_is_not_promoted_to_employer_fact(
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
        "Software Engineer in Tehran",
        "Software Engineer in London",
        "Living in Tehran",
        "Based in London",
        "ساکن تهران",
    ),
)
def test_location_language_does_not_create_employer(
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
        "Works at Tehran",
        "Works at London",
        "مهندس نرم افزار در تهران",
        "مهندس نرم افزار در ایران",
    ),
)
def test_obvious_location_only_values_are_rejected(
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
        "Student at Tehran University",
        "Researcher at Tehran University",
        "Works at Tehran University",
        "Software Engineer at Example University",
        "Software Engineer at Example Institute",
        "Software Engineer at Example Academy",
        "دانشجوی دانشگاه تهران",
        "مهندس نرم افزار در دانشگاه تهران",
        "مهندس نرم افزار در موسسه آموزش عالی",
        "مهندس نرم افزار در آکادمی نمونه",
    ),
)
def test_educational_institution_is_not_employer_fact(
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
        "Former Software Engineer at Acme",
        "Previously Software Engineer at Acme",
        "Formerly Software Engineer at Acme",
        "Used to work at Acme",
        "Worked at Acme",
        "Worked with Acme",
    ),
)
def test_historical_english_employment_is_rejected(
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
        "سابق مهندس نرم افزار در دیجی کالا",
        "قبلا مهندس نرم افزار در دیجی کالا",
        "قبلاً مهندس نرم افزار در دیجی کالا",
        "قبلاً در دیجی کالا کار می کردم",
        "قبلاً در دیجی کالا کار می‌کردم",
    ),
)
def test_historical_persian_employment_is_rejected(
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
        "Hiring Software Engineer at Acme",
        "Looking for Software Engineer at Acme",
        "Recruiting Software Engineer at Acme",
        "Seeking Product Designer at Acme",
    ),
)
def test_recruiting_context_is_not_employer_claim(
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
        "استخدام مهندس نرم افزار در دیجی کالا",
        "به دنبال مهندس نرم افزار در دیجی کالا",
        "نیازمند مهندس نرم افزار در دیجی کالا",
    ),
)
def test_persian_recruiting_context_is_not_employer_claim(
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
        "Founder of Acme",
        "Co-founder of Acme",
        "Co Founder of Acme",
        "بنیانگذار Acme",
        "هم بنیانگذار Acme",
        "هم‌بنیانگذار Acme",
    ),
)
def test_founder_relation_is_not_employer_fact(
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
        "Freelance Developer",
        "Self-employed Developer",
        "Self employed Developer",
        "Consultant for Acme",
        "Freelance Developer for Acme",
    ),
)
def test_non_employment_work_relation_does_not_create_employer(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


def test_pipe_stops_employer_capture() -> None:
    assert values(
        "Software Engineer at Acme | Photographer",
    ) == {
        "acme",
    }


def test_comma_stops_employer_capture() -> None:
    assert values(
        "Software Engineer at Acme, Tehran",
    ) == {
        "acme",
    }


def test_semicolon_stops_employer_capture() -> None:
    assert values(
        "Software Engineer at Acme; Photographer",
    ) == {
        "acme",
    }


def test_persian_separator_stops_employer_capture() -> None:
    assert values(
        "مهندس نرم افزار در دیجی کالا، عکاس",
    ) == {
        "دیجی کالا",
    }


def test_multiple_explicit_employer_claims_are_retained() -> None:
    assert values(
        "Works at Acme | Software Engineer at Veyra",
    ) == {
        "acme",
        "veyra",
    }


def test_duplicate_employer_claim_is_deduplicated() -> None:
    evidence = BioEmployerExtractor().extract(
        "Works at Acme | Software Engineer at Acme",
    )

    assert len(evidence) == 1
    assert evidence[0].normalized_value == "acme"


@pytest.mark.parametrize(
    "text",
    (
        "Software Engineer at https://acme.com",
        "Software Engineer at www.acme.com",
    ),
)
def test_url_is_not_promoted_to_employer_fact(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


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
        BioEmployerExtractor(
            confidence=confidence,
        )
