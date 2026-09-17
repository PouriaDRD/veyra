"""Hardening tests for education degree and institution extraction."""

import pytest

from veyra.domain.evidence import (
    BioEducationExtractor,
    BioInstitutionExtractor,
)


def education_values(text: str) -> set[str]:
    """Return normalized EDUCATION evidence values."""

    return {str(item.normalized_value) for item in BioEducationExtractor().extract(text)}


def institution_values(text: str) -> set[str]:
    """Return normalized INSTITUTION evidence values."""

    return {str(item.normalized_value) for item in BioInstitutionExtractor().extract(text)}


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("BSc", {"bachelor"}),
        ("B.Sc.", {"bachelor"}),
        ("MSc", {"master"}),
        ("M.Sc.", {"master"}),
        ("PhD", {"doctorate"}),
        ("Ph.D.", {"doctorate"}),
        ("DPhil", {"doctorate"}),
        ("Bachelor", {"bachelor"}),
        ("Master's", {"master"}),
        ("Doctorate", {"doctorate"}),
        ("Associate Degree", {"associate"}),
        ("BEng", {"bachelor:engineering"}),
        ("MEng", {"master:engineering"}),
        ("BBA", {"bachelor:business administration"}),
        ("MBA", {"master:business administration"}),
        ("کارشناسی", {"bachelor"}),
        ("کارشناسی ارشد", {"master"}),
        ("فوق لیسانس", {"master"}),
        ("دکتری", {"doctorate"}),
        ("کاردانی", {"associate"}),
    ),
)
def test_safe_degree_only_segments_are_supported(
    text: str,
    expected: set[str],
) -> None:
    assert education_values(text) == expected


@pytest.mark.parametrize(
    "text",
    (
        "Master Chef",
        "Master of Ceremonies",
        "Bachelor party",
        "Bachelor pad",
        "Master of None",
        "BA",
        "MA",
        "BS",
        "MS",
        "BA | London",
        "MA | Tehran",
    ),
)
def test_ambiguous_or_non_academic_degree_like_text_is_rejected(
    text: str,
) -> None:
    assert education_values(text) == set()


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("BEng Software Engineering", {"bachelor:software engineering"}),
        ("MEng Computer Engineering", {"master:computer engineering"}),
        ("DPhil in Philosophy", {"doctorate:philosophy"}),
        ("BA in History", {"bachelor:history"}),
        ("MA in Economics", {"master:economics"}),
    ),
)
def test_additional_field_bearing_abbreviations_are_supported(
    text: str,
    expected: set[str],
) -> None:
    assert education_values(text) == expected


@pytest.mark.parametrize(
    ("text", "education", "institution"),
    (
        (
            "BSc Computer Science at MIT",
            {"bachelor:computer science"},
            {"mit"},
        ),
        (
            "MSc Data Science from Stanford University",
            {"master:data science"},
            {"stanford university"},
        ),
        (
            "PhD at MIT",
            {"doctorate"},
            {"mit"},
        ),
        (
            "MBA from Harvard University",
            {"master:business administration"},
            {"harvard university"},
        ),
        (
            "کارشناسی مهندسی نرم افزار در دانشگاه تهران",
            {"bachelor:مهندسی نرم افزار"},
            {"دانشگاه تهران"},
        ),
        (
            "کارشناسی ارشد علوم داده از دانشگاه شریف",
            {"master:علوم داده"},
            {"دانشگاه شریف"},
        ),
        (
            "دکتری در دانشگاه تهران",
            {"doctorate"},
            {"دانشگاه تهران"},
        ),
    ),
)
def test_degree_and_institution_can_be_extracted_from_same_segment(
    text: str,
    education: set[str],
    institution: set[str],
) -> None:
    assert education_values(text) == education
    assert institution_values(text) == institution


def test_degree_only_profile_segment_inside_bio_is_supported() -> None:
    assert education_values(
        "Software Engineer | MSc | Tehran",
    ) == {
        "master",
    }


def test_ambiguous_short_form_inside_bio_is_not_supported() -> None:
    assert (
        education_values(
            "Designer | MA | London",
        )
        == set()
    )


def test_field_bearing_credential_wins_over_degree_only_interpretation() -> None:
    assert education_values(
        "MSc Data Science",
    ) == {
        "master:data science",
    }


def test_word_degree_requires_academic_connector_for_field() -> None:
    assert (
        education_values(
            "Master Photographer",
        )
        == set()
    )


def test_degree_institution_relation_does_not_pollute_field() -> None:
    assert education_values(
        "Master's in AI from Stanford University",
    ) == {
        "master:ai",
    }


def test_degree_institution_relation_keeps_institution_separate() -> None:
    assert institution_values(
        "Master's in AI from Stanford University",
    ) == {
        "stanford university",
    }
