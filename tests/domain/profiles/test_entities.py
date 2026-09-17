"""Tests for profile domain entities."""

from datetime import UTC, datetime

import pytest

from veyra.domain.profiles import Profile, SocialPlatform


def test_profile_is_created_with_normalized_username() -> None:
    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123456",
        username="  @PouriaDRD  ",
    )

    assert profile.external_id == "123456"
    assert profile.username == "PouriaDRD"


def test_profile_requires_external_id() -> None:
    with pytest.raises(
        ValueError,
        match="external_id must not be empty",
    ):
        Profile(
            platform=SocialPlatform.INSTAGRAM,
            external_id=" ",
            username="pouria",
        )


def test_profile_can_change_username() -> None:
    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123",
        username="old_name",
    )

    changed_at = datetime(
        2026,
        9,
        17,
        12,
        0,
        tzinfo=UTC,
    )

    profile.change_username(
        "@new_name",
        changed_at=changed_at,
    )

    assert profile.username == "new_name"
    assert profile.updated_at == changed_at
