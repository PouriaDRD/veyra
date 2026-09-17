"""Tests for location hypothesis strategy."""

from veyra.domain.evidence import (
    Evidence,
    EvidenceSource,
    FactKind,
    FactResolver,
    FactStatus,
)
from veyra.domain.intelligence import (
    EvidenceNature,
    EvidenceStrength,
    HypothesisEngine,
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
    HypothesisStatus,
    LocationSignal,
    LocationSignalKind,
)
from veyra.domain.intelligence.location_strategy import (
    LIKELY_LOCATION_HYPOTHESIS_DEFINITION,
    LocationHypothesisAdapter,
)


def build_city_evidence(
    value: str,
    *,
    confidence: float = 0.96,
) -> Evidence:
    """Build explicit city evidence."""

    return Evidence(
        source=EvidenceSource.BIO,
        raw_value=value,
        normalized_value=value,
        confidence=confidence,
        extractor="test_city",
        nature=EvidenceNature.EXPLICIT,
        strength=EvidenceStrength.VERY_STRONG,
    )


def evaluate(
    observations: tuple[
        HypothesisObservation,
        ...,
    ],
) -> HypothesisResult:
    """Evaluate location observations."""

    return HypothesisEngine().evaluate(
        LIKELY_LOCATION_HYPOTHESIS_DEFINITION,
        observations,
    )


def test_strategy_is_open_set() -> None:
    assert LIKELY_LOCATION_HYPOTHESIS_DEFINITION.allow_observed_values is True

    assert LIKELY_LOCATION_HYPOTHESIS_DEFINITION.kind is HypothesisKind.LIKELY_LOCATION


def test_explicit_city_fact_becomes_strong_observation() -> None:
    fact = FactResolver().resolve(
        FactKind.CITY,
        (
            build_city_evidence(
                "tehran",
            ),
        ),
    )

    assert fact.status is FactStatus.SUPPORTED

    observations = LocationHypothesisAdapter().from_fact(
        fact,
    )

    result = evaluate(
        observations,
    )

    assert result.best_value == "tehran"

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_unknown_city_fact_produces_no_observation() -> None:
    fact = FactResolver().resolve(
        FactKind.CITY,
        (),
    )

    assert (
        LocationHypothesisAdapter().from_fact(
            fact,
        )
        == ()
    )


def test_geotag_supports_dynamic_location_candidate() -> None:
    observations = LocationHypothesisAdapter().from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="tehran",
                weight=0.75,
                confidence=0.9,
            ),
        )
    )

    result = evaluate(
        observations,
    )

    assert result.best_value == "tehran"

    assert (
        result.candidate_for(
            "tehran",
        )
        is not None
    )


def test_profile_metadata_is_stronger_than_bio_mention() -> None:
    adapter = LocationHypothesisAdapter()

    metadata = adapter.from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.PROFILE_METADATA,
                value="tehran",
                weight=1.0,
                confidence=1.0,
            ),
        )
    )

    bio = adapter.from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.BIO_MENTION,
                value="tehran",
                weight=1.0,
                confidence=1.0,
            ),
        )
    )

    metadata_result = evaluate(
        metadata,
    )

    bio_result = evaluate(
        bio,
    )

    metadata_candidate = metadata_result.candidate_for(
        "tehran",
    )

    bio_candidate = bio_result.candidate_for(
        "tehran",
    )

    assert metadata_candidate is not None
    assert bio_candidate is not None

    assert metadata_candidate.score > bio_candidate.score


def test_multiple_geotags_reinforce_same_location() -> None:
    adapter = LocationHypothesisAdapter()

    observations = adapter.from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="tehran",
                weight=0.75,
                confidence=0.9,
            ),
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="tehran",
                weight=0.75,
                confidence=0.9,
            ),
        )
    )

    result = evaluate(
        observations,
    )

    tehran = result.candidate_for(
        "tehran",
    )

    assert tehran is not None

    assert tehran.score > 0.75


def test_different_contextual_locations_are_not_hard_conflict() -> None:
    adapter = LocationHypothesisAdapter()

    observations = adapter.from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="tehran",
                weight=0.75,
                confidence=0.9,
            ),
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="karaj",
                weight=0.75,
                confidence=0.9,
            ),
        )
    )

    result = evaluate(
        observations,
    )

    assert result.status is HypothesisStatus.AMBIGUOUS

    assert result.best_value == "unknown"


def test_competing_explicit_city_claims_are_conflicted() -> None:
    fact = FactResolver().resolve(
        FactKind.CITY,
        (
            build_city_evidence(
                "tehran",
            ),
            build_city_evidence(
                "shiraz",
            ),
        ),
    )

    assert fact.status is FactStatus.CONFLICTED

    observations = LocationHypothesisAdapter().from_fact(
        fact,
    )

    result = evaluate(
        observations,
    )

    assert result.status is HypothesisStatus.CONFLICTED


def test_explicit_city_outweighs_weaker_contextual_location() -> None:
    fact = FactResolver().resolve(
        FactKind.CITY,
        (
            build_city_evidence(
                "tehran",
            ),
        ),
    )

    adapter = LocationHypothesisAdapter()

    observations = adapter.combine(
        city_fact=fact,
        signals=(
            LocationSignal(
                kind=LocationSignalKind.CAPTION_MENTION,
                value="shiraz",
                weight=0.25,
                confidence=0.8,
            ),
        ),
    )

    result = evaluate(
        observations,
    )

    assert result.best_value == "tehran"

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_persian_and_english_normalized_location_share_candidate() -> None:
    adapter = LocationHypothesisAdapter()

    observations = adapter.from_signals(
        (
            LocationSignal(
                kind=LocationSignalKind.BIO_MENTION,
                value="tehran",
                weight=0.35,
                confidence=0.9,
                context="تهران",
            ),
            LocationSignal(
                kind=LocationSignalKind.GEOTAG,
                value="tehran",
                weight=0.75,
                confidence=0.9,
                context="Tehran",
            ),
        )
    )

    result = evaluate(
        observations,
    )

    candidates = tuple(candidate.value for candidate in result.candidates)

    assert (
        candidates.count(
            "tehran",
        )
        == 1
    )

    assert result.best_value == "tehran"
