"""Tests for contextual biography location-signal extraction."""

import pytest

from veyra.domain.intelligence import (
    LocationRelation,
    LocationSignalKind,
)
from veyra.domain.intelligence.location_signal_extractor import (
    BioLocationSignalExtractor,
)


def values(
    bio: str,
) -> set[str]:
    """Return normalized location signal values."""

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
        "📍 Tehran",
        "ساکن تهران",
        "مقیم تهران",
        "📍 تهران",
    ),
)
def test_current_location_claims_do_not_duplicate_as_signals(
    bio: str,
) -> None:
    assert (
        BioLocationSignalExtractor().extract(
            bio,
        )
        == ()
    )


@pytest.mark.parametrize(
    ("bio", "expected"),
    (
        (
            "From Tehran",
            "tehran",
        ),
        (
            "Born in Shiraz",
            "shiraz",
        ),
        (
            "اهل تهران",
            "tehran",
        ),
        (
            "متولد شیراز",
            "shiraz",
        ),
    ),
)
def test_origin_claims_become_origin_signals(
    bio: str,
    expected: str,
) -> None:
    signals = BioLocationSignalExtractor().extract(
        bio,
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    signal = signals[0]

    assert signal.value == expected

    assert signal.kind is LocationSignalKind.BIO_MENTION

    assert signal.relation is LocationRelation.ORIGIN

    assert signal.weight == 0.20
    assert signal.confidence == 0.90


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


@pytest.mark.parametrize(
    "bio",
    (
        "Tehran University",
        "University of Tehran",
        "Tehran College",
        "Tehran Institute",
        "دانشگاه تهران",
    ),
)
def test_institutional_mentions_are_not_location_signals(
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
        "Tehrani designer",
        "Iranian developer",
    ),
)
def test_location_aliases_do_not_match_inside_other_words(
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

    assert signal.relation is LocationRelation.CONTEXTUAL_MENTION

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


def test_current_location_wins_over_same_city_origin_signal() -> None:
    signals = BioLocationSignalExtractor().extract(
        "From Tehran | Based in Tehran",
    )

    assert signals == ()


def test_origin_and_different_current_city_are_preserved_separately() -> None:
    signals = BioLocationSignalExtractor().extract(
        "From Shiraz | Based in Tehran",
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    signal = signals[0]

    assert signal.value == "shiraz"

    assert signal.relation is LocationRelation.ORIGIN


def test_persian_origin_and_current_city_are_preserved_separately() -> None:
    signals = BioLocationSignalExtractor().extract(
        "اهل شیراز | ساکن تهران",
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    signal = signals[0]

    assert signal.value == "shiraz"

    assert signal.relation is LocationRelation.ORIGIN


def test_travel_occurrence_does_not_hide_separate_contextual_occurrence() -> None:
    signals = BioLocationSignalExtractor().extract(
        "Traveling to Tehran | Tehran photographer",
    )

    assert (
        len(
            signals,
        )
        == 1
    )

    assert signals[0].value == "tehran"

    assert signals[0].relation is LocationRelation.CONTEXTUAL_MENTION
