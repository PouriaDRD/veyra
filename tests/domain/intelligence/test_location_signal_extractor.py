"""Tests for contextual biography location-signal extraction."""

import pytest

from veyra.domain.intelligence import LocationSignalKind
from veyra.domain.intelligence.location_signal_extractor import (
    BioLocationSignalExtractor,
)


def values(
    bio: str,
) -> set[str]:
    """Return normalized contextual location values."""

    return {
        signal.value
        for signal in BioLocationSignalExtractor().extract(
            bio,
        )
    }


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        (
            "I love Tehran food",
            {"tehran"},
        ),
        (
            "Designer | Tehran",
            {"tehran"},
        ),
        (
            "تهران و قهوه",
            {"tehran"},
        ),
        (
            "عاشق شیراز و موسیقی",
            {"shiraz"},
        ),
        (
            "Tech | Tehran | Python",
            {"tehran"},
        ),
    ),
)
def test_extracts_contextual_city_mentions(
    bio: str,
    expected: set[str],
) -> None:
    assert (
        values(
            bio,
        )
        == expected
    )


@pytest.mark.parametrize(
    "bio",
    (
        "Based in Tehran",
        "Living in Tehran",
        "From Tehran",
        "📍 Tehran",
        "ساکن تهران",
        "اهل تهران",
        "مقیم تهران",
        "📍 تهران",
    ),
)
def test_explicit_city_claims_do_not_duplicate_as_signals(
    bio: str,
) -> None:
    assert (
        BioLocationSignalExtractor().extract(
            bio,
        )
        == ()
    )


@pytest.mark.parametrize(
    "bio",
    (
        "Traveling to Tehran",
        "Travelling to Tehran",
        "Trip to Tehran",
        "Visited Tehran",
        "Visiting Tehran",
        "سفر به تهران",
        "مسافرت به تهران",
        "قبلاً ساکن تهران",
        "قبلا ساکن تهران",
    ),
)
def test_travel_and_historical_mentions_are_ignored(
    bio: str,
) -> None:
    assert (
        BioLocationSignalExtractor().extract(
            bio,
        )
        == ()
    )


def test_signal_semantics() -> None:
    signals = BioLocationSignalExtractor().extract(
        "عاشق تهران",
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    signal = signals[0]

    assert signal.kind is LocationSignalKind.BIO_MENTION

    assert signal.value == "tehran"
    assert signal.weight == 0.35
    assert signal.confidence == 0.85
    assert signal.context == "عاشق تهران"


def test_persian_and_english_mentions_normalize_equally() -> None:
    persian = BioLocationSignalExtractor().extract(
        "عاشق تهران",
    )

    english = BioLocationSignalExtractor().extract(
        "I love Tehran",
    )

    assert persian
    assert english

    assert persian[0].value == english[0].value == "tehran"


def test_multiple_contextual_cities_are_preserved() -> None:
    signals = BioLocationSignalExtractor().extract(
        "Tehran | Karaj",
    )

    assert {signal.value for signal in signals} == {
        "tehran",
        "karaj",
    }
