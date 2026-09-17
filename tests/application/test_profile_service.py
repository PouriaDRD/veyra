"""Tests for ProfileService."""

from uuid import uuid4

import pytest

from veyra.application.dto import CreateProfileCommand
from veyra.application.exceptions import (
    EntityNotFoundError,
    ProfileAlreadyExistsError,
)
from veyra.application.services import ProfileService
from veyra.domain.profiles import SocialPlatform

from .fakes import FakeUnitOfWork


def test_profile_service_creates_profile() -> None:
    unit_of_work = FakeUnitOfWork()

    service = ProfileService(
        unit_of_work,
    )

    profile = service.create(
        CreateProfileCommand(
            platform=SocialPlatform.INSTAGRAM,
            external_id="123456",
            username="@veyra_user",
        )
    )

    assert profile.username == "veyra_user"
    assert unit_of_work.profiles.get_by_id(profile.id) == profile
    assert unit_of_work.commit_count == 1


def test_profile_service_rejects_duplicate_external_identity() -> None:
    unit_of_work = FakeUnitOfWork()

    service = ProfileService(
        unit_of_work,
    )

    command = CreateProfileCommand(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123456",
        username="veyra_user",
    )

    service.create(command)

    with pytest.raises(
        ProfileAlreadyExistsError,
    ):
        service.create(command)

    assert unit_of_work.rollback_count == 1


def test_profile_service_changes_username() -> None:
    unit_of_work = FakeUnitOfWork()

    service = ProfileService(
        unit_of_work,
    )

    profile = service.create(
        CreateProfileCommand(
            platform=SocialPlatform.INSTAGRAM,
            external_id="123",
            username="old_name",
        )
    )

    updated = service.change_username(
        profile.id,
        "@new_name",
    )

    assert updated.username == "new_name"


def test_profile_service_raises_for_missing_profile() -> None:
    service = ProfileService(
        FakeUnitOfWork(),
    )

    with pytest.raises(
        EntityNotFoundError,
        match="Profile",
    ):
        service.get(
            uuid4(),
        )
