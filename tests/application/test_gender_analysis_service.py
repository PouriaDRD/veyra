"""Tests for declared-gender analysis integration."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import (
    DeclaredGender,
    FactKind,
    FactStatus,
)
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def test_analysis_resolves_declared_female_fact() -> None:
    result = ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="candidate1997",
            bio="بانو | Software Engineer",
            is_private=True,
        ),
        reference_date=REFERENCE_DATE,
    )

    gender = result.fact_for(
        FactKind.DECLARED_GENDER,
    )

    assert gender is not None
    assert gender.status is FactStatus.SUPPORTED
    assert gender.value == DeclaredGender.FEMALE.value
    assert gender.confidence == 0.99


def test_analysis_returns_unknown_gender_when_bio_has_no_explicit_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="candidate1997",
            bio="Software Engineer | Tehran",
            is_private=True,
        ),
        reference_date=REFERENCE_DATE,
    )

    gender = result.fact_for(
        FactKind.DECLARED_GENDER,
    )

    assert gender is not None
    assert gender.status is FactStatus.UNKNOWN
    assert gender.value is None


def test_analysis_preserves_conflicting_declared_gender_evidence() -> None:
    result = ProfileAnalysisService().analyze(
        ProfileSnapshot(
            profile_id=uuid4(),
            username="candidate1997",
            bio="she/her | he/him",
            is_private=True,
        ),
        reference_date=REFERENCE_DATE,
    )

    gender = result.fact_for(
        FactKind.DECLARED_GENDER,
    )

    assert gender is not None
    assert gender.status is FactStatus.CONFLICTED
    assert gender.value is None
