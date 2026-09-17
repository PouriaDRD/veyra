"""Profile application services."""

from uuid import UUID

from veyra.application.dto import CreateProfileCommand
from veyra.application.exceptions import (
    EntityNotFoundError,
    ProfileAlreadyExistsError,
)
from veyra.application.ports import UnitOfWork
from veyra.domain.profiles import Profile


class ProfileService:
    """Application use cases for persistent social profiles."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._unit_of_work = unit_of_work

    def create(
        self,
        command: CreateProfileCommand,
    ) -> Profile:
        """
        Register a newly discovered social profile.

        Social identity is unique by platform + external identifier.
        """

        external_id = command.external_id.strip()

        with self._unit_of_work as unit_of_work:
            existing = unit_of_work.profiles.get_by_external_identity(
                command.platform,
                external_id,
            )

            if existing is not None:
                raise ProfileAlreadyExistsError(
                    platform=command.platform.value,
                    external_id=external_id,
                )

            profile = Profile(
                platform=command.platform,
                external_id=external_id,
                username=command.username,
            )

            unit_of_work.profiles.add(profile)

            return profile

    def get(
        self,
        profile_id: UUID,
    ) -> Profile:
        """Return a profile or raise an application-level error."""

        with self._unit_of_work as unit_of_work:
            profile = unit_of_work.profiles.get_by_id(
                profile_id,
            )

            if profile is None:
                raise EntityNotFoundError(
                    "Profile",
                    profile_id,
                )

            return profile

    def change_username(
        self,
        profile_id: UUID,
        username: str,
    ) -> Profile:
        """Change the current username of a persisted profile."""

        with self._unit_of_work as unit_of_work:
            profile = unit_of_work.profiles.get_by_id(
                profile_id,
            )

            if profile is None:
                raise EntityNotFoundError(
                    "Profile",
                    profile_id,
                )

            profile.change_username(
                username,
            )

            unit_of_work.profiles.update(
                profile,
            )

            return profile
