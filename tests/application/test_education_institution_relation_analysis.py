"""Application integration tests for education/institution relations."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.domain.evidence import FactKind, FactStatus
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(2026, 9, 17)


def analyze(bio: str | None) -> ProfileAnalysisResult:
    """Analyze one profile bio."""

    return ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="relation_test_1997",
            display_name=None,
            bio=bio,
        ),
        reference_date=REFERENCE_DATE,
    )


def test_analysis_exposes_one_explicit_relation() -> None:
    result = analyze(
        "BSc Computer Science at MIT",
    )

    assert len(result.education_institution_relations) == 1

    relation = result.education_institution_relations[0]

    assert relation.education == "bachelor:computer science"
    assert relation.institution == "mit"
    assert relation.confidence == 0.97


def test_analysis_exposes_multiple_explicit_relations() -> None:
    result = analyze(
        "BSc Computer Science at MIT | MSc Data Science at Stanford University",
    )

    assert tuple(
        (
            relation.education,
            relation.institution,
        )
        for relation in result.education_institution_relations
    ) == (
        (
            "bachelor:computer science",
            "mit",
        ),
        (
            "master:data science",
            "stanford university",
        ),
    )


def test_unrelated_segments_do_not_create_relation() -> None:
    result = analyze(
        "BSc Computer Science | Student at MIT",
    )

    assert result.education_institution_relations == ()


def test_absent_bio_has_no_relations() -> None:
    result = analyze(
        None,
    )

    assert result.education_institution_relations == ()


def test_relation_does_not_replace_education_or_institution_facts() -> None:
    result = analyze(
        "BSc Computer Science at MIT",
    )

    education = result.fact_for(
        FactKind.EDUCATION,
    )
    institution = result.fact_for(
        FactKind.INSTITUTION,
    )

    assert education is not None
    assert institution is not None

    assert education.status is FactStatus.SUPPORTED
    assert education.values == ("bachelor:computer science",)

    assert institution.status is FactStatus.SUPPORTED
    assert institution.values == ("mit",)


def test_relation_does_not_add_flat_evidence_item() -> None:
    result = analyze(
        "BSc Computer Science at MIT",
    )

    extractors = {item.extractor for item in result.evidence}

    assert "bio_education_institution_explicit" not in extractors
    assert "bio_education_explicit" in extractors
    assert "bio_institution_explicit" in extractors


def test_education_relations_for_filters_by_education_value() -> None:
    result = analyze(
        "BSc Computer Science at MIT | MSc Data Science at Stanford University",
    )

    relations = result.education_relations_for(
        "master:data science",
    )

    assert len(relations) == 1
    assert relations[0].institution == "stanford university"
