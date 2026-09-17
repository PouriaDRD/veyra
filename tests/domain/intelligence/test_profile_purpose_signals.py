"""Tests for multilingual profile-purpose signal extraction."""

import pytest

from veyra.domain.intelligence import ProfilePurpose
from veyra.domain.intelligence.profile_purpose_signals import (
    ProfilePurposeSignalExtractor,
)


def purposes(
    text: str,
) -> set[ProfilePurpose]:
    """Extract supported purpose candidates."""

    return {
        signal.purpose
        for signal in ProfilePurposeSignalExtractor().extract(
            text,
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
        "shopify developer",
    ),
)
def test_markers_do_not_match_inside_longer_words(
    text: str,
) -> None:
    extracted = purposes(
        text,
    )

    if text == "shopify developer":
        assert extracted == {
            ProfilePurpose.PROFESSIONAL,
        }
        return

    assert extracted == set()


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
