"""Tests for profile-purpose hypothesis strategy."""

import pytest

from veyra.domain.intelligence import (
    HypothesisEngine,
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
    HypothesisStatus,
    ObservationPolarity,
    ProfilePurpose,
    ProfilePurposeSignalKind,
)
from veyra.domain.intelligence.profile_purpose import (
    ProfilePurposeSignal,
)
from veyra.domain.intelligence.profile_purpose_strategy import (
    PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
    PROFILE_PURPOSE_HYPOTHESIS_STRATEGY,
    ProfilePurposeHypothesisAdapter,
    ProfilePurposeHypothesisStrategy,
)


def build_signal(
    *,
    kind: ProfilePurposeSignalKind,
    purpose: ProfilePurpose,
    weight: float,
    confidence: float,
    raw_value: str,
) -> ProfilePurposeSignal:
    """Build one purpose-signal fixture."""

    return ProfilePurposeSignal(
        kind=kind,
        purpose=purpose,
        weight=weight,
        confidence=confidence,
        raw_value=raw_value,
    )


def build_observation(
    *,
    purpose: ProfilePurpose,
    weight: float,
    confidence: float = 1.0,
    source: str,
    correlation_key: str,
) -> HypothesisObservation:
    """Build one normalized profile-purpose observation."""

    return HypothesisObservation(
        target_value=purpose.value,
        polarity=ObservationPolarity.SUPPORT,
        weight=weight,
        confidence=confidence,
        source=source,
        explanation=(f"Supports {purpose.value}."),
        correlation_key=correlation_key,
        conflict_eligible=False,
    )


def evaluate_prepared(
    observations: tuple[
        HypothesisObservation,
        ...,
    ],
) -> HypothesisResult:
    """Prepare profile-purpose observations and evaluate them."""

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    return HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
        prepared,
    )


def test_definition_uses_profile_purpose_kind() -> None:
    assert PROFILE_PURPOSE_HYPOTHESIS_DEFINITION.kind is HypothesisKind.PROFILE_PURPOSE


def test_strategy_uses_profile_purpose_kind() -> None:
    assert PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.kind is HypothesisKind.PROFILE_PURPOSE


def test_definition_contains_all_profile_purpose_values() -> None:
    assert set(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION.allowed_values,
    ) == {purpose.value for purpose in ProfilePurpose}


def test_professional_signal_supports_professional_profile() -> None:
    observations = ProfilePurposeHypothesisAdapter().from_signals(
        (
            build_signal(
                kind=(ProfilePurposeSignalKind.PROFESSIONAL_ROLE),
                purpose=ProfilePurpose.PROFESSIONAL,
                weight=0.65,
                confidence=0.90,
                raw_value="software engineer",
            ),
        )
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.PROFESSIONAL.value

    assert result.status is HypothesisStatus.PROBABLE


def test_business_signal_is_strongly_supported() -> None:
    observations = ProfilePurposeHypothesisAdapter().from_signals(
        (
            build_signal(
                kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
                purpose=ProfilePurpose.BUSINESS,
                weight=0.90,
                confidence=0.95,
                raw_value="online shop",
            ),
        )
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.BUSINESS.value

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_business_outweighs_professional_role_when_correlated() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            source="bio:professional",
            correlation_key="bio",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.BUSINESS.value


def test_creator_and_business_same_source_remain_ambiguous() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="bio:creator",
            correlation_key="bio",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.status is HypothesisStatus.AMBIGUOUS

    assert result.best_value == ProfilePurpose.UNKNOWN.value


def test_independent_creator_and_business_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="display_name:creator",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.MIXED.value

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_independent_professional_and_creator_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            source="display_name:professional",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="bio:creator",
            correlation_key="bio",
        ),
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.MIXED.value

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_independent_business_and_organization_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="display_name:business",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.ORGANIZATION,
            weight=0.90,
            confidence=0.95,
            source="bio:organization",
            correlation_key="bio",
        ),
    )

    result = evaluate_prepared(
        observations,
    )

    assert result.best_value == ProfilePurpose.MIXED.value


def test_personal_and_professional_do_not_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PERSONAL,
            weight=0.85,
            confidence=0.95,
            source="display_name:personal",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            source="bio:professional",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    assert all(observation.target_value != ProfilePurpose.MIXED.value for observation in prepared)


def test_two_independent_same_purpose_signals_do_not_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="display_name:creator",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="bio:creator",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    assert all(observation.target_value == ProfilePurpose.CREATOR.value for observation in prepared)


def test_weak_independent_observations_do_not_become_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.49,
            source="display_name:professional",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.49,
            source="bio:creator",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    assert all(observation.target_value != ProfilePurpose.MIXED.value for observation in prepared)


def test_opposition_does_not_participate_in_mixed() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            source="display_name:creator",
            correlation_key="display-name",
        ),
        HypothesisObservation(
            target_value=ProfilePurpose.BUSINESS.value,
            polarity=ObservationPolarity.OPPOSE,
            weight=0.90,
            confidence=0.95,
            source="bio:business-opposition",
            explanation="Opposes business.",
            correlation_key="bio",
            conflict_eligible=False,
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    assert all(observation.target_value != ProfilePurpose.MIXED.value for observation in prepared)


def test_mixed_derivation_preserves_underlying_correlation_groups() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="display_name:creator",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    mixed = tuple(
        observation
        for observation in prepared
        if (observation.target_value == ProfilePurpose.MIXED.value)
    )

    assert len(mixed) == 2

    assert {observation.correlation_key for observation in mixed} == {
        "display-name",
        "bio",
    }


def test_mixed_derivation_preserves_weight_and_confidence() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="display_name:creator",
            correlation_key="display-name",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            confidence=0.95,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    mixed = tuple(
        observation
        for observation in prepared
        if (observation.target_value == ProfilePurpose.MIXED.value)
    )

    assert {
        (
            observation.weight,
            observation.confidence,
        )
        for observation in mixed
    } == {
        (
            0.85,
            0.95,
        ),
        (
            0.90,
            0.95,
        ),
    }


def test_strongest_independent_pair_is_selected() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.60,
            source="profile:professional",
            correlation_key="profile",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.80,
            source="display:creator",
            correlation_key="display",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    prepared = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    mixed_sources = {
        observation.source
        for observation in prepared
        if (observation.target_value == ProfilePurpose.MIXED.value)
    }

    assert mixed_sources == {
        "display:creator",
        "bio:business",
    }


def test_mixed_pair_selection_is_order_invariant() -> None:
    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            source="profile:professional",
            correlation_key="profile",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            source="display:creator",
            correlation_key="display",
        ),
        build_observation(
            purpose=ProfilePurpose.BUSINESS,
            weight=0.90,
            source="bio:business",
            correlation_key="bio",
        ),
    )

    forward = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        observations,
    )

    reverse = PROFILE_PURPOSE_HYPOTHESIS_STRATEGY.prepare_observations(
        reversed(
            observations,
        )
    )

    forward_mixed = {
        observation.source
        for observation in forward
        if (observation.target_value == ProfilePurpose.MIXED.value)
    }

    reverse_mixed = {
        observation.source
        for observation in reverse
        if (observation.target_value == ProfilePurpose.MIXED.value)
    }

    assert forward_mixed == reverse_mixed


def test_custom_mixed_threshold_is_respected() -> None:
    strategy = ProfilePurposeHypothesisStrategy(
        mixed_min_effective_strength=0.80,
    )

    observations = (
        build_observation(
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            source="display:professional",
            correlation_key="display",
        ),
        build_observation(
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            source="bio:creator",
            correlation_key="bio",
        ),
    )

    prepared = strategy.prepare_observations(
        observations,
    )

    assert all(observation.target_value != ProfilePurpose.MIXED.value for observation in prepared)


@pytest.mark.parametrize(
    "threshold",
    (
        -0.01,
        1.01,
    ),
)
def test_rejects_invalid_mixed_threshold(
    threshold: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="mixed_min_effective_strength",
    ):
        ProfilePurposeHypothesisStrategy(
            mixed_min_effective_strength=threshold,
        )


def test_no_signals_returns_unknown() -> None:
    result = evaluate_prepared(
        (),
    )

    assert result.status is HypothesisStatus.UNKNOWN

    assert result.best_value == ProfilePurpose.UNKNOWN.value


def test_adapter_preserves_signal_semantics() -> None:
    signal = build_signal(
        kind=ProfilePurposeSignalKind.CREATOR_MARKER,
        purpose=ProfilePurpose.CREATOR,
        weight=0.85,
        confidence=0.95,
        raw_value="content creator",
    )

    observations = ProfilePurposeHypothesisAdapter().from_signals(
        (signal,),
        source="bio",
        correlation_key="profile-purpose:test:bio",
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.target_value == ProfilePurpose.CREATOR.value

    assert observation.weight == 0.85
    assert observation.confidence == 0.95

    assert observation.source == "profile_purpose_signal:bio:creator_marker"

    assert observation.correlation_key == "profile-purpose:test:bio"

    assert observation.conflict_eligible is False


def test_same_source_can_share_correlation_key() -> None:
    signals = (
        build_signal(
            kind=ProfilePurposeSignalKind.PROFESSIONAL_ROLE,
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            raw_value="designer",
        ),
        build_signal(
            kind=ProfilePurposeSignalKind.CREATOR_MARKER,
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            raw_value="creator",
        ),
    )

    observations = ProfilePurposeHypothesisAdapter().from_signals(
        signals,
        source="bio",
        correlation_key="profile-purpose:test:bio",
    )

    assert {observation.correlation_key for observation in observations} == {
        "profile-purpose:test:bio",
    }


def test_without_shared_key_each_signal_gets_own_correlation_key() -> None:
    signals = (
        build_signal(
            kind=ProfilePurposeSignalKind.PROFESSIONAL_ROLE,
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=0.65,
            confidence=0.90,
            raw_value="designer",
        ),
        build_signal(
            kind=ProfilePurposeSignalKind.CREATOR_MARKER,
            purpose=ProfilePurpose.CREATOR,
            weight=0.85,
            confidence=0.95,
            raw_value="creator",
        ),
    )

    observations = ProfilePurposeHypothesisAdapter().from_signals(
        signals,
    )

    keys = {observation.correlation_key for observation in observations}

    assert len(keys) == 2
    assert None not in keys


def test_rejects_empty_observation_source() -> None:
    with pytest.raises(
        ValueError,
        match="source",
    ):
        ProfilePurposeHypothesisAdapter().from_signals(
            (),
            source="   ",
        )
