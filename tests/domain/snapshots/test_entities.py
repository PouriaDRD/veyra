"""Tests for profile snapshot entities."""

from uuid import uuid4

import pytest

from veyra.domain.snapshots import ProfileSnapshot


def test_snapshot_accepts_unknown_counts() -> None:
    snapshot = ProfileSnapshot(
        profile_id=uuid4(),
        username="profile",
    )

    assert snapshot.followers_count is None
    assert snapshot.following_count is None
    assert snapshot.posts_count is None


def test_snapshot_normalizes_optional_text() -> None:
    snapshot = ProfileSnapshot(
        profile_id=uuid4(),
        username="@profile",
        display_name="  Test Profile  ",
        bio="   ",
    )

    assert snapshot.username == "profile"
    assert snapshot.display_name == "Test Profile"
    assert snapshot.bio is None


def test_snapshot_rejects_negative_counts() -> None:
    with pytest.raises(
        ValueError,
        match="followers_count must not be negative",
    ):
        ProfileSnapshot(
            profile_id=uuid4(),
            username="profile",
            followers_count=-1,
        )
