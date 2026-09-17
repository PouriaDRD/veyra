"""Tests for profile-purpose hypothesis strategy."""

import pytest

from veyra.domain.intelligence import (
    HypothesisEngine,
    HypothesisKind,
    HypothesisStatus,
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


def test_definition_uses_profile_purpose_kind() -> None:
    assert PROFILE_PURPOSE_HYPOTHESIS_DEFINITION.kind is HypothesisKind.PROFILE_PURPOSE


def test_static_strategy_uses_profile_purpose_kind() -> None:
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

    result = HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
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

    result = HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
        observations,
    )

    assert result.best_value == ProfilePurpose.BUSINESS.value

    assert result.status is HypothesisStatus.STRONGLY_SUPPORTED


def test_business_outweighs_professional_role() -> None:
    observations = ProfilePurposeHypothesisAdapter().from_signals(
        (
            build_signal(
                kind=(ProfilePurposeSignalKind.PROFESSIONAL_ROLE),
                purpose=ProfilePurpose.PROFESSIONAL,
                weight=0.65,
                confidence=0.90,
                raw_value="designer",
            ),
            build_signal(
                kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
                purpose=ProfilePurpose.BUSINESS,
                weight=0.90,
                confidence=0.95,
                raw_value="shop",
            ),
        )
    )

    result = HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
        observations,
    )

    assert result.best_value == ProfilePurpose.BUSINESS.value


def test_creator_and_business_can_remain_ambiguous() -> None:
    observations = ProfilePurposeHypothesisAdapter().from_signals(
        (
            build_signal(
                kind=ProfilePurposeSignalKind.CREATOR_MARKER,
                purpose=ProfilePurpose.CREATOR,
                weight=0.85,
                confidence=0.95,
                raw_value="content creator",
            ),
            build_signal(
                kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
                purpose=ProfilePurpose.BUSINESS,
                weight=0.90,
                confidence=0.95,
                raw_value="shop",
            ),
        )
    )

    result = HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
        observations,
    )

    assert result.status is HypothesisStatus.AMBIGUOUS

    assert result.best_value == ProfilePurpose.UNKNOWN.value


def test_no_signals_returns_unknown() -> None:
    result = HypothesisEngine().evaluate(
        PROFILE_PURPOSE_HYPOTHESIS_DEFINITION,
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

    assert (
        len(
            observations,
        )
        == 1
    )

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
