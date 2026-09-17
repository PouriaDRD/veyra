"""Tests for multilingual text normalization."""

import pytest

from veyra.domain.intelligence import normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (
            "\u0643\u064a\u0627",
            "\u06a9\u06cc\u0627",
        ),
        (
            "\u06a9\u06cc\u0627",
            "\u06a9\u06cc\u0627",
        ),
        (
            "\u06f1\u06f3\u06f8\u06f8",
            "1388",
        ),
        (
            "\u0661\u0663\u0668\u0668",
            "1388",
        ),
        (
            "  Married   ",
            "married",
        ),
        (
            "MARRIED",
            "married",
        ),
        (
            "Single",
            "single",
        ),
        (
            "\u0645\u062a\u0627\u0647\u0644",
            "\u0645\u062a\u0627\u0647\u0644",
        ),
        (
            "\u0645\u062a\u0623\u0647\u0644",
            "\u0645\u062a\u0623\u0647\u0644",
        ),
        (
            "Ali\u200cReza",
            "ali reza",
        ),
        (
            "Ali\u200bReza",
            "ali reza",
        ),
        (
            "  Tehran   |   Iran  ",
            "tehran | iran",
        ),
        (
            "\u062a\u0647\u0631\u0627\u0646  Iran",
            "\u062a\u0647\u0631\u0627\u0646 iran",
        ),
    ),
)
def test_normalize_text_handles_multilingual_inputs(
    raw: str,
    expected: str,
) -> None:
    assert normalize_text(raw) == expected
