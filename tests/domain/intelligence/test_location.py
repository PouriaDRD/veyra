"""Tests for location intelligence domain values."""

import pytest

from veyra.domain.intelligence.location import (
    DEFAULT_LOCATION_LEXICON,
    LocationEntity,
    LocationEntityKind,
    LocationLexicon,
)


def test_default_lexicon_contains_persian_and_english_tehran() -> None:
    tehran = DEFAULT_LOCATION_LEXICON.find(
        kind=LocationEntityKind.CITY,
        value="tehran",
    )

    assert tehran is not None

    assert "Tehran".casefold() in {alias.casefold() for alias in tehran.aliases}

    assert "تهران" in tehran.aliases

    assert tehran.country_code == "IR"


def test_default_lexicon_contains_iran() -> None:
    iran = DEFAULT_LOCATION_LEXICON.find(
        kind=LocationEntityKind.COUNTRY,
        value="iran",
    )

    assert iran is not None
    assert "ایران" in iran.aliases
    assert iran.country_code == "IR"


def test_lexicon_filters_entries_by_kind() -> None:
    cities = DEFAULT_LOCATION_LEXICON.by_kind(
        LocationEntityKind.CITY,
    )

    countries = DEFAULT_LOCATION_LEXICON.by_kind(
        LocationEntityKind.COUNTRY,
    )

    assert cities
    assert countries

    assert all(item.kind is LocationEntityKind.CITY for item in cities)

    assert all(item.kind is LocationEntityKind.COUNTRY for item in countries)


def test_location_entity_normalizes_value_and_country_code() -> None:
    entity = LocationEntity(
        kind=LocationEntityKind.CITY,
        value="  London ",
        display_name=" London ",
        aliases=(
            "London",
            "لندن",
        ),
        country_code="gb",
    )

    assert entity.value == "london"
    assert entity.display_name == "London"
    assert entity.country_code == "GB"


def test_location_entity_rejects_invalid_country_code() -> None:
    with pytest.raises(
        ValueError,
        match="two-letter",
    ):
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="london",
            display_name="London",
            aliases=("London",),
            country_code="GBR",
        )


def test_lexicon_rejects_duplicate_entities() -> None:
    entity = LocationEntity(
        kind=LocationEntityKind.CITY,
        value="test",
        display_name="Test",
        aliases=("Test",),
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        LocationLexicon(
            entries=(
                entity,
                entity,
            )
        )
