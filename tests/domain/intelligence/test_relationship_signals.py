"""Tests for contextual relationship signals."""

import pytest

from veyra.domain.intelligence import (
    RelationshipSignalExtractor,
    RelationshipSignalKind,
)


@pytest.fixture
def extractor() -> RelationshipSignalExtractor:
    """Create relationship signal extractor."""

    return RelationshipSignalExtractor()


@pytest.mark.parametrize(
    ("text", "expected_kind"),
    (
        (
            "💍",
            RelationshipSignalKind.RING_EMOJI,
        ),
        (
            "❤️",
            RelationshipSignalKind.RED_HEART_EMOJI,
        ),
        (
            "❤",
            RelationshipSignalKind.RED_HEART_EMOJI,
        ),
        (
            "Ali ❤️",
            RelationshipSignalKind.NAME_ADJACENT_HEART,
        ),
        (
            "❤️ Ali",
            RelationshipSignalKind.NAME_ADJACENT_HEART,
        ),
        (
            "Sara 💍",
            RelationshipSignalKind.NAME_ADJACENT_RING,
        ),
        (
            "💍 Sara",
            RelationshipSignalKind.NAME_ADJACENT_RING,
        ),
        (
            "علی ❤️",
            RelationshipSignalKind.NAME_ADJACENT_HEART,
        ),
        (
            "❤️ علی",
            RelationshipSignalKind.NAME_ADJACENT_HEART,
        ),
        (
            "سارا 💍",
            RelationshipSignalKind.NAME_ADJACENT_RING,
        ),
        (
            "💍 سارا",
            RelationshipSignalKind.NAME_ADJACENT_RING,
        ),
    ),
)
def test_basic_relationship_signals_support_persian_and_english(
    extractor: RelationshipSignalExtractor,
    text: str,
    expected_kind: RelationshipSignalKind,
) -> None:
    signals = extractor.extract(
        text,
    )

    assert signals

    assert any(signal.kind is expected_kind for signal in signals)


def test_name_adjacent_ring_is_stronger_than_plain_ring(
    extractor: RelationshipSignalExtractor,
) -> None:
    plain = extractor.extract("💍")

    named = extractor.extract("Sara 💍")

    assert named[0].weight > plain[0].weight


def test_ring_is_stronger_than_red_heart(
    extractor: RelationshipSignalExtractor,
) -> None:
    ring = extractor.extract("💍")

    heart = extractor.extract("❤️")

    assert ring[0].weight > heart[0].weight


def test_name_adjacent_heart_is_stronger_than_plain_heart(
    extractor: RelationshipSignalExtractor,
) -> None:
    plain = extractor.extract("❤️")

    named = extractor.extract("Ali ❤️")

    assert named[0].weight > plain[0].weight


def test_name_adjacent_ring_is_stronger_than_name_adjacent_heart(
    extractor: RelationshipSignalExtractor,
) -> None:
    ring = extractor.extract("Sara 💍")

    heart = extractor.extract("Sara ❤️")

    assert ring[0].weight > heart[0].weight


def test_ring_and_red_heart_combination_strengthens_plain_ring(
    extractor: RelationshipSignalExtractor,
) -> None:
    plain_ring = extractor.extract("💍")

    combined = extractor.extract("💍 ❤️")

    ring_signal = next(
        signal for signal in combined if signal.kind is RelationshipSignalKind.RING_EMOJI
    )

    assert ring_signal.weight > plain_ring[0].weight


@pytest.mark.parametrize(
    "text",
    (
        "Ali ❤️",
        "ALI ❤️",
        "ali ❤️",
        "Ali❤️",
        "❤️Ali",
        "علی ❤️",
        "علی❤️",
        "❤️علی",
        "سارا 💍",
        "سارا💍",
        "💍سارا",
    ),
)
def test_name_adjacent_signals_survive_spacing_and_case_variations(
    extractor: RelationshipSignalExtractor,
    text: str,
) -> None:
    assert extractor.extract(
        text,
    )


@pytest.mark.parametrize(
    "text",
    (
        "love ❤️",
        "music ❤️",
        "coffee ❤️",
        "python ❤️",
        "django ❤️",
        "developer ❤️",
        "gym ❤️",
        "travel ❤️",
        "family ❤️",
        "work ❤️",
        "tehran ❤️",
        "iran ❤️",
        "عشق ❤️",
        "زندگی ❤️",
        "موسیقی ❤️",
        "قهوه ❤️",
        "ورزش ❤️",
        "سفر ❤️",
        "خانواده ❤️",
        "کار ❤️",
        "تهران ❤️",
        "ایران ❤️",
    ),
)
def test_known_non_person_words_do_not_become_name_adjacent_hearts(
    extractor: RelationshipSignalExtractor,
    text: str,
) -> None:
    signals = extractor.extract(
        text,
    )

    assert all(signal.kind is not RelationshipSignalKind.NAME_ADJACENT_HEART for signal in signals)


@pytest.mark.parametrize(
    "text",
    (
        "music 💍",
        "coffee 💍",
        "python 💍",
        "developer 💍",
        "work 💍",
        "tehran 💍",
        "iran 💍",
        "موسیقی 💍",
        "قهوه 💍",
        "کار 💍",
        "تهران 💍",
        "ایران 💍",
    ),
)
def test_known_non_person_words_do_not_become_name_adjacent_rings(
    extractor: RelationshipSignalExtractor,
    text: str,
) -> None:
    signals = extractor.extract(
        text,
    )

    assert all(signal.kind is not RelationshipSignalKind.NAME_ADJACENT_RING for signal in signals)


def test_non_person_red_heart_still_remains_generic_contextual_signal(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("music ❤️")

    assert any(signal.kind is RelationshipSignalKind.RED_HEART_EMOJI for signal in signals)

    assert all(signal.kind is not RelationshipSignalKind.NAME_ADJACENT_HEART for signal in signals)


def test_non_person_ring_still_remains_plain_ring_signal(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("music 💍")

    assert any(signal.kind is RelationshipSignalKind.RING_EMOJI for signal in signals)

    assert all(signal.kind is not RelationshipSignalKind.NAME_ADJACENT_RING for signal in signals)


@pytest.mark.parametrize(
    "heart",
    (
        "💕",
        "💖",
        "💗",
        "💓",
        "💞",
        "💘",
        "💝",
        "💟",
    ),
)
def test_generic_hearts_are_detected(
    extractor: RelationshipSignalExtractor,
    heart: str,
) -> None:
    signals = extractor.extract(
        heart,
    )

    assert len(signals) == 1

    assert signals[0].kind is RelationshipSignalKind.HEART_EMOJI

    assert signals[0].weight == extractor.generic_heart_weight


@pytest.mark.parametrize(
    "heart",
    (
        "🤍",
        "🖤",
        "💙",
        "💚",
        "💛",
        "💜",
        "🩷",
        "🩵",
        "🩶",
        "🤎",
    ),
)
def test_decorative_hearts_have_lower_weight(
    extractor: RelationshipSignalExtractor,
    heart: str,
) -> None:
    signals = extractor.extract(
        heart,
    )

    assert len(signals) == 1

    assert signals[0].kind is RelationshipSignalKind.HEART_EMOJI

    assert signals[0].weight == extractor.decorative_heart_weight

    assert signals[0].weight < extractor.red_heart_weight


def test_duplicate_red_hearts_do_not_duplicate_signal_kind(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("❤️ ❤️ ❤️")

    red_heart_signals = [
        signal for signal in signals if signal.kind is RelationshipSignalKind.RED_HEART_EMOJI
    ]

    assert (
        len(
            red_heart_signals,
        )
        == 1
    )


def test_duplicate_rings_do_not_duplicate_signal_kind(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("💍 💍 💍")

    ring_signals = [
        signal for signal in signals if signal.kind is RelationshipSignalKind.RING_EMOJI
    ]

    assert (
        len(
            ring_signals,
        )
        == 1
    )


def test_duplicate_named_hearts_do_not_duplicate_signal_kind(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("Ali ❤️ Sara ❤️")

    named = [
        signal for signal in signals if signal.kind is RelationshipSignalKind.NAME_ADJACENT_HEART
    ]

    assert len(named) == 1


def test_duplicate_named_rings_do_not_duplicate_signal_kind(
    extractor: RelationshipSignalExtractor,
) -> None:
    signals = extractor.extract("Ali 💍 Sara 💍")

    named = [
        signal for signal in signals if signal.kind is RelationshipSignalKind.NAME_ADJACENT_RING
    ]

    assert len(named) == 1


@pytest.mark.parametrize(
    "text",
    (
        "",
        " ",
        "Developer",
        "Tehran",
        "تهران",
        "Python Django",
        "Photography",
        "Software Engineer",
        "برنامه نویس",
    ),
)
def test_unrelated_text_produces_no_relationship_signals(
    extractor: RelationshipSignalExtractor,
    text: str,
) -> None:
    assert (
        extractor.extract(
            text,
        )
        == ()
    )


def test_context_is_preserved(
    extractor: RelationshipSignalExtractor,
) -> None:
    text = "Developer | Sara 💍 | Tehran"

    signals = extractor.extract(
        text,
    )

    assert signals

    assert all(signal.context is not None for signal in signals)


def test_signal_weights_are_not_probabilities(
    extractor: RelationshipSignalExtractor,
) -> None:
    """
    Ensure defaults remain semantic strengths rather than certainty claims.
    """

    assert extractor.name_adjacent_ring_weight < 1.0

    assert extractor.name_adjacent_heart_weight < extractor.name_adjacent_ring_weight

    assert extractor.red_heart_weight < extractor.ring_weight
