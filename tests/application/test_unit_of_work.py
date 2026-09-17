"""Tests for the in-memory application Unit of Work."""

import pytest

from veyra.domain.profiles import Profile, SocialPlatform

from .fakes import FakeUnitOfWork


def test_fake_unit_of_work_commits_successful_changes() -> None:
    unit_of_work = FakeUnitOfWork()

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="commit-test",
        username="commit_test",
    )

    with unit_of_work:
        unit_of_work.profiles.add(
            profile,
        )

    assert (
        unit_of_work.profiles.get_by_id(
            profile.id,
        )
        == profile
    )

    assert unit_of_work.commit_count == 1
    assert unit_of_work.rollback_count == 0


def test_fake_unit_of_work_restores_state_on_rollback() -> None:
    unit_of_work = FakeUnitOfWork()

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="rollback-test",
        username="rollback_test",
    )

    with (
        pytest.raises(
            RuntimeError,
            match="forced failure",
        ),
        unit_of_work,
    ):
        unit_of_work.profiles.add(
            profile,
        )

        raise RuntimeError(
            "forced failure",
        )

    assert (
        unit_of_work.profiles.get_by_id(
            profile.id,
        )
        is None
    )

    assert unit_of_work.commit_count == 0
    assert unit_of_work.rollback_count == 1
