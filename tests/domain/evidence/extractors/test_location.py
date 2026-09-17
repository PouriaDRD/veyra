"""Tests for multilingual explicit location extraction."""

import pytest

from veyra.domain.evidence import (
    FactKind,
)
from veyra.domain.evidence.extractors import (
    BioLocationExtractor,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
)


def normalized_values(
    bio: str,
) -> set[str]:
    """Extract normalized string values from one biography."""

    evidence = BioLocationExtractor().extract(
        bio,
    )

    return {
        item.normalized_value
        for item in evidence
        if isinstance(
            item.normalized_value,
            str,
        )
    }


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        (
            "Based in Tehran",
            {"tehran"},
        ),
        (
            "Living in Tehran",
            {"tehran"},
        ),
        (
            "From Shiraz",
            {"shiraz"},
        ),
        (
            "📍 Tehran",
            {"tehran"},
        ),
        (
            "ساکن تهران",
            {"tehran"},
        ),
        (
            "اهل شیراز",
            {"shiraz"},
        ),
        (
            "مقیم کرج",
            {"karaj"},
        ),
        (
            "📍 اصفهان",
            {"isfahan"},
        ),
    ),
)
def test_extracts_explicit_city_claims(
    bio: str,
    expected: set[str],
) -> None:
    assert (
        normalized_values(
            bio,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        (
            "Tehran, Iran",
            {
                "tehran",
                "iran",
            },
        ),
        (
            "تهران، ایران",
            {
                "tehran",
                "iran",
            },
        ),
        (
            "Iran | Tehran",
            {
                "iran",
                "tehran",
            },
        ),
        (
            "Graphic Designer | تهران، Iran",
            {
                "tehran",
                "iran",
            },
        ),
    ),
)
def test_extracts_compact_city_country_pairs(
    bio: str,
    expected: set[str],
) -> None:
    assert (
        normalized_values(
            bio,
        )
        == expected
    )


def test_extracts_persian_country_claim() -> None:
    evidence = BioLocationExtractor().extract(
        "ساکن ایران",
    )

    assert (
        len(
            evidence,
        )
        == 1
    )

    assert evidence[0].normalized_value == "iran"


def test_explicit_evidence_has_correct_semantics() -> None:
    evidence = BioLocationExtractor().extract(
        "ساکن تهران",
    )

    assert (
        len(
            evidence,
        )
        == 1
    )

    item = evidence[0]

    assert item.confidence == 0.96

    assert item.nature is EvidenceNature.EXPLICIT

    assert item.strength is EvidenceStrength.VERY_STRONG

    assert item.extractor == "bio_location_explicit"


def test_compact_pair_uses_slightly_lower_confidence() -> None:
    evidence = BioLocationExtractor().extract(
        "Tehran, Iran",
    )

    assert evidence

    assert all(item.confidence == 0.92 for item in evidence)


@pytest.mark.parametrize(
    "bio",
    (
        "Traveling to Tehran",
        "Travelling to Tehran",
        "Trip to Tehran",
        "Visited Tehran",
        "Visiting Tehran",
        "سفر به تهران",
        "مسافرت به شیراز",
    ),
)
def test_travel_mentions_do_not_become_location_facts(
    bio: str,
) -> None:
    assert (
        BioLocationExtractor().extract(
            bio,
        )
        == ()
    )


@pytest.mark.parametrize(
    "bio",
    (
        "Not in Tehran",
        "Used to live in Tehran",
        "Formerly based in Tehran",
        "قبلاً ساکن تهران",
        "قبلا ساکن تهران",
    ),
)
def test_non_current_location_claims_are_ignored(
    bio: str,
) -> None:
    assert (
        BioLocationExtractor().extract(
            bio,
        )
        == ()
    )


def test_bare_city_mention_is_not_explicit_fact() -> None:
    assert BioLocationExtractor().extract("I love Tehran food") == ()


def test_city_kind_filter_returns_only_city() -> None:
    evidence = BioLocationExtractor().extract_for_kind(
        "Tehran, Iran",
        kind=FactKind.CITY,
    )

    assert (
        len(
            evidence,
        )
        == 1
    )

    assert evidence[0].normalized_value == "tehran"


def test_country_kind_filter_returns_only_country() -> None:
    evidence = BioLocationExtractor().extract_for_kind(
        "Tehran, Iran",
        kind=FactKind.COUNTRY,
    )

    assert (
        len(
            evidence,
        )
        == 1
    )

    assert evidence[0].normalized_value == "iran"


def test_rejects_unsupported_fact_kind_filter() -> None:
    with pytest.raises(
        ValueError,
        match="CITY and COUNTRY",
    ):
        BioLocationExtractor().extract_for_kind(
            "Tehran, Iran",
            kind=FactKind.OCCUPATION,
        )


def test_persian_and_english_forms_normalize_equally() -> None:
    persian = BioLocationExtractor().extract_for_kind(
        "ساکن تهران",
        kind=FactKind.CITY,
    )

    english = BioLocationExtractor().extract_for_kind(
        "Based in Tehran",
        kind=FactKind.CITY,
    )

    assert persian
    assert english

    assert persian[0].normalized_value == english[0].normalized_value == "tehran"
