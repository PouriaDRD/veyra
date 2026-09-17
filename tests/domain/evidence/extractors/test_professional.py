"""Tests for explicit professional occupation evidence extraction."""

import pytest

from veyra.domain.evidence import (
    DEFAULT_OCCUPATION_LEXICON,
    EvidenceSource,
    OccupationEntry,
    OccupationLexicon,
    ProfileOccupationExtractor,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
)


def values(
    text: str,
    *,
    source: str = "bio",
) -> set[str]:
    """Extract normalized occupation values."""

    return {
        str(item.normalized_value)
        for item in ProfileOccupationExtractor().extract(
            text,
            source=source,  # type: ignore[arg-type]
        )
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Software Engineer", {"software engineer"}),
        ("مهندس نرم افزار", {"software engineer"}),
        ("مهندس نرم‌افزار", {"software engineer"}),
        ("Software Developer", {"software developer"}),
        ("توسعه دهنده", {"software developer"}),
        ("Programmer", {"programmer"}),
        ("برنامه نویس", {"programmer"}),
        ("Data Analyst", {"data analyst"}),
        ("تحلیلگر داده", {"data analyst"}),
        ("Business Analyst", {"business analyst"}),
        ("تحلیلگر کسب و کار", {"business analyst"}),
        ("Product Manager", {"product manager"}),
        ("مدیر محصول", {"product manager"}),
        ("Product Designer", {"product designer"}),
        ("طراح محصول", {"product designer"}),
        ("Graphic Designer", {"graphic designer"}),
        ("طراح گرافیک", {"graphic designer"}),
        ("Doctor", {"doctor"}),
        ("پزشک", {"doctor"}),
        ("Lawyer", {"lawyer"}),
        ("وکیل", {"lawyer"}),
        ("Architect", {"architect"}),
        ("معمار", {"architect"}),
        ("Photographer", {"photographer"}),
        ("عکاس", {"photographer"}),
    ),
)
def test_extracts_multilingual_explicit_occupation(
    text: str,
    expected: set[str],
) -> None:
    assert (
        values(
            text,
        )
        == expected
    )


def test_can_extract_more_than_one_explicit_role() -> None:
    assert values(
        "Software Engineer | Photographer",
    ) == {
        "software engineer",
        "photographer",
    }


def test_longer_specific_role_wins_over_generic_alias() -> None:
    assert values(
        "Product Designer",
    ) == {
        "product designer",
    }


def test_software_engineer_does_not_also_emit_generic_engineer() -> None:
    assert values(
        "Software Engineer",
    ) == {
        "software engineer",
    }


def test_freelance_role_remains_valid_occupation() -> None:
    assert values(
        "Freelance Developer",
    ) == {
        "software developer",
    }


def test_self_employed_without_explicit_role_does_not_create_occupation() -> None:
    assert (
        values(
            "Self-employed",
        )
        == set()
    )


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "Coffee | Tehran | Music",
        "Python enthusiast",
        "engineering notes",
        "developerly",
    ),
)
def test_unrelated_text_returns_no_occupation(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


def test_bio_evidence_uses_bio_source() -> None:
    evidence = ProfileOccupationExtractor().extract(
        "Software Engineer",
        source="bio",
    )

    assert len(evidence) == 1

    item = evidence[0]

    assert item.source is EvidenceSource.BIO
    assert item.confidence == 0.96
    assert item.extractor == "bio_occupation_explicit"


def test_display_name_evidence_uses_display_name_source() -> None:
    evidence = ProfileOccupationExtractor().extract(
        "Software Engineer",
        source="display_name",
    )

    assert len(evidence) == 1

    item = evidence[0]

    assert item.source is EvidenceSource.DISPLAY_NAME
    assert item.confidence == 0.92
    assert item.extractor == "display_name_occupation_explicit"


def test_occupation_is_explicit_very_strong_evidence() -> None:
    item = ProfileOccupationExtractor().extract(
        "Software Engineer",
        source="bio",
    )[0]

    assert item.nature is EvidenceNature.EXPLICIT
    assert item.strength is EvidenceStrength.VERY_STRONG


def test_raw_profile_text_is_retained() -> None:
    text = "Software Engineer | Python"

    item = ProfileOccupationExtractor().extract(
        text,
        source="bio",
    )[0]

    assert item.raw_value == text


@pytest.mark.parametrize(
    "text",
    (
        "Former Software Engineer",
        "Formerly Software Engineer",
        "Previously Software Engineer",
        "Aspiring Software Engineer",
        "Future Software Engineer",
    ),
)
def test_non_current_english_role_is_not_current_occupation(
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
        "سابق مهندس نرم افزار",
        "قبلا مهندس نرم افزار",
        "قبلاً مهندس نرم افزار",
    ),
)
def test_non_current_persian_role_is_not_current_occupation(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


def test_student_context_does_not_become_current_occupation() -> None:
    assert (
        values(
            "Student Software Engineer",
        )
        == set()
    )


def test_persian_student_context_does_not_become_current_occupation() -> None:
    assert (
        values(
            "دانشجوی مهندس نرم افزار",
        )
        == set()
    )


@pytest.mark.parametrize(
    "text",
    (
        "Hiring Software Engineer",
        "Looking for Software Engineer",
        "Seeking Software Engineer",
        "Need a Software Engineer",
    ),
)
def test_recruiting_text_does_not_become_occupation(
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
        "استخدام مهندس نرم افزار",
        "به دنبال مهندس نرم افزار",
        "نیازمند مهندس نرم افزار",
    ),
)
def test_persian_recruiting_text_does_not_become_occupation(
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
        "Not a Software Engineer",
        "Not Software Engineer",
        "Never been a Software Engineer",
    ),
)
def test_negated_english_role_is_not_occupation(
    text: str,
) -> None:
    assert (
        values(
            text,
        )
        == set()
    )


def test_negated_persian_role_is_not_occupation() -> None:
    assert (
        values(
            "مهندس نرم افزار نیستم",
        )
        == set()
    )


def test_default_lexicon_resolves_persian_alias() -> None:
    entry = DEFAULT_OCCUPATION_LEXICON.find_by_alias(
        "مهندس نرم افزار",
    )

    assert entry is not None
    assert entry.value == "software engineer"


def test_default_lexicon_resolves_persian_half_space_alias() -> None:
    entry = DEFAULT_OCCUPATION_LEXICON.find_by_alias(
        "مهندس نرم‌افزار",
    )

    assert entry is not None
    assert entry.value == "software engineer"


def test_default_lexicon_resolves_english_alias_case_insensitively() -> None:
    entry = DEFAULT_OCCUPATION_LEXICON.find_by_alias(
        "SOFTWARE ENGINEER",
    )

    assert entry is not None
    assert entry.value == "software engineer"


def test_unknown_alias_returns_none() -> None:
    assert (
        DEFAULT_OCCUPATION_LEXICON.find_by_alias(
            "rocket scientist",
        )
        is None
    )


def test_rejects_empty_occupation_value() -> None:
    with pytest.raises(
        ValueError,
        match="value",
    ):
        OccupationEntry(
            value="   ",
            aliases=("developer",),
        )


def test_rejects_empty_alias_collection() -> None:
    with pytest.raises(
        ValueError,
        match="aliases",
    ):
        OccupationEntry(
            value="developer",
            aliases=(),
        )


def test_rejects_duplicate_aliases_inside_entry() -> None:
    with pytest.raises(
        ValueError,
        match="unique",
    ):
        OccupationEntry(
            value="developer",
            aliases=(
                "developer",
                "Developer",
            ),
        )


def test_rejects_duplicate_canonical_values() -> None:
    with pytest.raises(
        ValueError,
        match="values",
    ):
        OccupationLexicon(
            entries=(
                OccupationEntry(
                    value="developer",
                    aliases=("developer",),
                ),
                OccupationEntry(
                    value="Developer",
                    aliases=("coder",),
                ),
            )
        )


def test_rejects_alias_collision_between_entries() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate occupation alias",
    ):
        OccupationLexicon(
            entries=(
                OccupationEntry(
                    value="developer",
                    aliases=("coder",),
                ),
                OccupationEntry(
                    value="programmer",
                    aliases=("Coder",),
                ),
            )
        )


@pytest.mark.parametrize(
    "confidence",
    (
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_bio_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        ProfileOccupationExtractor(
            bio_confidence=confidence,
        )


@pytest.mark.parametrize(
    "confidence",
    (
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_display_name_confidence(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        ProfileOccupationExtractor(
            display_name_confidence=confidence,
        )


def test_rejects_unsupported_source() -> None:
    with pytest.raises(
        ValueError,
        match="source",
    ):
        ProfileOccupationExtractor().extract(
            "Software Engineer",
            source="caption",  # type: ignore[arg-type]
        )
