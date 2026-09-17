"""End-to-end tests for profile location intelligence."""

from datetime import date
from uuid import uuid4

from veyra.application import ProfileAnalysisService
from veyra.domain.evidence import (
    FactKind,
    FactStatus,
)
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisStatus,
)
from veyra.domain.snapshots import ProfileSnapshot

REFERENCE_DATE = date(
    2026,
    9,
    17,
)


def build_snapshot(
    *,
    bio: str,
) -> ProfileSnapshot:
    """Create a profile snapshot for location analysis tests."""

    return ProfileSnapshot(
        profile_id=uuid4(),
        username="location_test_1997",
        bio=bio,
    )


def test_explicit_persian_city_becomes_fact_and_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="طراح | ساکن تهران",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert city is not None
    assert hypothesis is not None

    assert city.status is FactStatus.SUPPORTED
    assert city.value == "tehran"

    assert hypothesis.best_value == "tehran"

    assert hypothesis.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_explicit_english_city_becomes_fact() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Software Engineer | Based in Tehran",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    assert city is not None
    assert city.status is FactStatus.SUPPORTED
    assert city.value == "tehran"


def test_city_country_pair_resolves_both_facts() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Tehran, Iran",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    country = result.fact_for(
        FactKind.COUNTRY,
    )

    assert city is not None
    assert country is not None

    assert city.status is FactStatus.SUPPORTED
    assert country.status is FactStatus.SUPPORTED

    assert city.value == "tehran"
    assert country.value == "iran"


def test_contextual_persian_city_does_not_become_fact() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="عاشق تهران و قهوه",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert city is not None
    assert hypothesis is not None

    assert city.status is FactStatus.UNKNOWN
    assert city.value is None

    assert hypothesis.best_value == "tehran"

    assert hypothesis.status is HypothesisStatus.POSSIBLE


def test_contextual_english_city_does_not_become_fact() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="I love Tehran food",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert city is not None
    assert hypothesis is not None

    assert city.status is FactStatus.UNKNOWN
    assert city.value is None

    assert hypothesis.best_value == "tehran"


def test_travel_location_does_not_become_fact_or_hypothesis() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="سفر به تهران",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert city is not None
    assert hypothesis is not None

    assert city.status is FactStatus.UNKNOWN
    assert city.value is None

    assert hypothesis.status is HypothesisStatus.UNKNOWN

    assert hypothesis.best_value == "unknown"


def test_two_contextual_locations_remain_ambiguous() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="Tehran | Karaj",
        ),
        reference_date=REFERENCE_DATE,
    )

    city = result.fact_for(
        FactKind.CITY,
    )

    hypothesis = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert city is not None
    assert hypothesis is not None

    assert city.status is FactStatus.UNKNOWN
    assert city.value is None

    assert hypothesis.status is HypothesisStatus.AMBIGUOUS

    assert hypothesis.best_value == "unknown"


def test_relationship_and_location_hypotheses_coexist() -> None:
    result = ProfileAnalysisService().analyze(
        build_snapshot(
            bio="متاهل | ساکن تهران",
        ),
        reference_date=REFERENCE_DATE,
    )

    relationship = result.hypothesis_for(
        HypothesisKind.RELATIONSHIP_STATUS,
    )

    location = result.hypothesis_for(
        HypothesisKind.LIKELY_LOCATION,
    )

    assert relationship is not None
    assert location is not None

    assert relationship.status is HypothesisStatus.STRONGLY_SUPPORTED

    assert location.status is HypothesisStatus.STRONGLY_SUPPORTED

    assert location.best_value == "tehran"
