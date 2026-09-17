"""Tests for source-aware multilingual profile-purpose extraction."""

import pytest

from veyra.domain.intelligence import ProfilePurpose
from veyra.domain.intelligence.profile_purpose_signals import (
    ProfilePurposeSignalExtractor,
)


def purposes(
    text: str,
    *,
    source: str = "bio",
) -> set[ProfilePurpose]:
    """Extract supported purpose candidates."""

    return {
        signal.purpose
        for signal in ProfilePurposeSignalExtractor().extract(
            text,
            source=source,  # type: ignore[arg-type]
        )
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        (
            "Software Engineer | Python",
            {ProfilePurpose.PROFESSIONAL},
        ),
        (
            "مهندس نرم افزار | پایتون",
            {ProfilePurpose.PROFESSIONAL},
        ),
        (
            "Content Creator | YouTuber",
            {ProfilePurpose.CREATOR},
        ),
        (
            "تولید محتوا | بلاگر",
            {ProfilePurpose.CREATOR},
        ),
        (
            "Online Shop | DM for order",
            {ProfilePurpose.BUSINESS},
        ),
        (
            "فروشگاه | ثبت سفارش",
            {ProfilePurpose.BUSINESS},
        ),
        (
            "Nonprofit Foundation",
            {ProfilePurpose.ORGANIZATION},
        ),
        (
            "بنیاد خیریه",
            {ProfilePurpose.ORGANIZATION},
        ),
        (
            "Personal account | my life",
            {ProfilePurpose.PERSONAL},
        ),
        (
            "پیج شخصی | روزمرگی",
            {ProfilePurpose.PERSONAL},
        ),
    ),
)
def test_extracts_multilingual_purpose_signals(
    text: str,
    expected: set[ProfilePurpose],
) -> None:
    assert (
        purposes(
            text,
        )
        == expected
    )


def test_business_and_professional_signals_can_coexist() -> None:
    extracted = purposes(
        "Software Engineer | Online Shop",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
        ProfilePurpose.BUSINESS,
    }


def test_creator_and_professional_signals_can_coexist() -> None:
    extracted = purposes(
        "Designer | Content Creator",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
        ProfilePurpose.CREATOR,
    }


def test_persian_business_and_professional_signals_can_coexist() -> None:
    extracted = purposes(
        "طراح گرافیک | فروشگاه | ثبت سفارش",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
        ProfilePurpose.BUSINESS,
    }


def test_persian_creator_and_professional_signals_can_coexist() -> None:
    extracted = purposes(
        "عکاس | تولید محتوا",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
        ProfilePurpose.CREATOR,
    }


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "Coffee | Tehran | Music",
        "سلام دنیا",
        "Python enthusiast",
    ),
)
def test_unrelated_text_produces_no_signal(
    text: str,
) -> None:
    assert (
        ProfilePurposeSignalExtractor().extract(
            text,
        )
        == ()
    )


@pytest.mark.parametrize(
    "text",
    (
        "development updates",
        "engineering notes",
        "designerly",
        "storehouse",
    ),
)
def test_markers_do_not_match_inside_longer_words(
    text: str,
) -> None:
    assert (
        purposes(
            text,
        )
        == set()
    )


def test_shopify_does_not_match_shop_but_developer_still_matches() -> None:
    assert purposes(
        "Shopify Developer",
    ) == {
        ProfilePurpose.PROFESSIONAL,
    }


def test_signal_retains_context() -> None:
    signals = ProfilePurposeSignalExtractor().extract(
        "Software Engineer | Python",
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    signal = signals[0]

    assert signal.raw_value == "software engineer"
    assert signal.context == "software engineer | python"


def test_mixed_persian_english_input_is_supported() -> None:
    extracted = purposes(
        "Software Engineer | تولید محتوا",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
        ProfilePurpose.CREATOR,
    }


# ============================================================
# BUSINESS HARDENING
# ============================================================


@pytest.mark.parametrize(
    "text",
    (
        "Business student",
        "MBA | Business student",
        "Studying business",
        "I work at Acme Company",
        "Employee at Acme Company",
    ),
)
def test_generic_business_words_in_bio_do_not_create_business_signal(
    text: str,
) -> None:
    assert ProfilePurpose.BUSINESS not in purposes(
        text,
        source="bio",
    )


def test_business_analyst_is_professional_not_business() -> None:
    extracted = purposes(
        "Business Analyst",
        source="bio",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
    }


def test_brand_designer_is_professional_not_business() -> None:
    extracted = purposes(
        "Brand Designer",
        source="bio",
    )

    assert extracted == {
        ProfilePurpose.PROFESSIONAL,
    }


@pytest.mark.parametrize(
    "text",
    (
        "Online Shop",
        "Online Store",
        "Official Store",
        "DM for order",
        "Orders open",
        "فروشگاه",
        "فروش آنلاین",
        "ثبت سفارش",
        "برای سفارش دایرکت",
    ),
)
def test_strong_commercial_intent_in_bio_is_business(
    text: str,
) -> None:
    assert ProfilePurpose.BUSINESS in purposes(
        text,
        source="bio",
    )


@pytest.mark.parametrize(
    "text",
    (
        "Acme Company",
        "Acme Brand",
        "Acme Store",
        "فروشگاه ویرا",
        "شرکت ویرا",
        "برند ویرا",
    ),
)
def test_display_name_can_identify_business(
    text: str,
) -> None:
    assert ProfilePurpose.BUSINESS in purposes(
        text,
        source="display_name",
    )


# ============================================================
# ORGANIZATION HARDENING
# ============================================================


@pytest.mark.parametrize(
    "text",
    (
        "Student at Tehran University",
        "Researcher at Tehran University",
        "Studying at Tehran University",
        "Teacher at Example Academy",
        "دانشجوی دانشگاه تهران",
        "استاد دانشگاه تهران",
    ),
)
def test_institution_mentions_in_bio_do_not_create_organization_signal(
    text: str,
) -> None:
    assert ProfilePurpose.ORGANIZATION not in purposes(
        text,
        source="bio",
    )


@pytest.mark.parametrize(
    "text",
    (
        "Tehran University",
        "Example Institute",
        "Open Learning Academy",
        "دانشگاه تهران",
        "موسسه ویرا",
        "آکادمی ویرا",
    ),
)
def test_display_name_can_identify_organization(
    text: str,
) -> None:
    assert ProfilePurpose.ORGANIZATION in purposes(
        text,
        source="display_name",
    )


@pytest.mark.parametrize(
    "text",
    (
        "Official account of Tehran University",
        "Official page of Example Institute",
        "صفحه رسمی دانشگاه تهران",
        "پیج رسمی موسسه ویرا",
    ),
)
def test_official_organization_bio_is_supported(
    text: str,
) -> None:
    assert ProfilePurpose.ORGANIZATION in purposes(
        text,
        source="bio",
    )


@pytest.mark.parametrize(
    "text",
    (
        "Nonprofit Foundation",
        "Nonprofit Organization",
        "NGO",
        "بنیاد خیریه",
        "موسسه خیریه",
        "سازمان مردم نهاد",
    ),
)
def test_strong_organization_identity_is_supported_in_bio(
    text: str,
) -> None:
    assert ProfilePurpose.ORGANIZATION in purposes(
        text,
        source="bio",
    )


# ============================================================
# SOURCE CONTRACT
# ============================================================


def test_default_source_is_bio() -> None:
    assert (
        ProfilePurposeSignalExtractor().extract(
            "Tehran University",
        )
        == ()
    )


def test_display_name_and_bio_have_different_semantics() -> None:
    extractor = ProfilePurposeSignalExtractor()

    bio = extractor.extract(
        "Tehran University",
        source="bio",
    )

    display_name = extractor.extract(
        "Tehran University",
        source="display_name",
    )

    assert bio == ()

    assert {signal.purpose for signal in display_name} == {
        ProfilePurpose.ORGANIZATION,
    }


def test_rejects_unknown_source() -> None:
    with pytest.raises(
        ValueError,
        match="source",
    ):
        ProfilePurposeSignalExtractor().extract(
            "Online Shop",
            source="caption",  # type: ignore[arg-type]
        )
