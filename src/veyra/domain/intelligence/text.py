"""Multilingual text normalization utilities."""

import re
import unicodedata

_PERSIAN_CHARACTER_TRANSLATION = str.maketrans(
    {
        "\u064a": "\u06cc",  # Arabic yeh -> Persian yeh
        "\u0649": "\u06cc",  # alef maksura -> Persian yeh
        "\u0643": "\u06a9",  # Arabic kaf -> Persian kaf
    }
)

_DIGIT_TRANSLATION = str.maketrans(
    {
        "\u06f0": "0",
        "\u06f1": "1",
        "\u06f2": "2",
        "\u06f3": "3",
        "\u06f4": "4",
        "\u06f5": "5",
        "\u06f6": "6",
        "\u06f7": "7",
        "\u06f8": "8",
        "\u06f9": "9",
        "\u0660": "0",
        "\u0661": "1",
        "\u0662": "2",
        "\u0663": "3",
        "\u0664": "4",
        "\u0665": "5",
        "\u0666": "6",
        "\u0667": "7",
        "\u0668": "8",
        "\u0669": "9",
    }
)

_ZERO_WIDTH_PATTERN = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")

_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(
    value: str,
    *,
    lowercase: bool = True,
) -> str:
    """
    Normalize Persian, Arabic, English, and mixed-language text.

    Operations:
    - Unicode NFKC normalization
    - Arabic/Persian letter normalization
    - Persian/Arabic digit normalization
    - zero-width character cleanup
    - whitespace normalization
    - optional Unicode-aware lowercase
    """

    normalized = unicodedata.normalize(
        "NFKC",
        value,
    )

    normalized = normalized.translate(
        _PERSIAN_CHARACTER_TRANSLATION,
    )

    normalized = normalized.translate(
        _DIGIT_TRANSLATION,
    )

    normalized = _ZERO_WIDTH_PATTERN.sub(
        " ",
        normalized,
    )

    normalized = _WHITESPACE_PATTERN.sub(
        " ",
        normalized,
    ).strip()

    if lowercase:
        normalized = normalized.casefold()

    return normalized
