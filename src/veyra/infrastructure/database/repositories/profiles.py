"""SQLAlchemy Profile repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from veyra.domain.profiles import Profile, SocialPlatform

from ..mappers import profile_to_domain, profile_to_model
from ..models import ProfileModel


class SqlAlchemyProfileRepository:
    """SQLAlchemy implementation of the Profile repository."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        profile: Profile,
    ) -> None:
        """Persist a new profile."""

        self._session.add(
            profile_to_model(profile),
        )

    def get_by_id(
        self,
        profile_id: UUID,
    ) -> Profile | None:
        """Return a profile by identifier."""

        model = self._session.get(
            ProfileModel,
            profile_id,
        )

        if model is None:
            return None

        return profile_to_domain(model)

    def get_by_external_identity(
        self,
        platform: SocialPlatform,
        external_id: str,
    ) -> Profile | None:
        """Return a profile by platform and external identifier."""

        model = self._session.scalar(
            select(ProfileModel).where(
                ProfileModel.platform == platform.value,
                ProfileModel.external_id == external_id.strip(),
            )
        )

        if model is None:
            return None

        return profile_to_domain(model)

    def get_by_username(
        self,
        platform: SocialPlatform,
        username: str,
    ) -> Profile | None:
        """Return a profile by platform and username."""

        normalized_username = username.strip().removeprefix("@").strip()

        model = self._session.scalar(
            select(ProfileModel).where(
                ProfileModel.platform == platform.value,
                ProfileModel.username == normalized_username,
            )
        )

        if model is None:
            return None

        return profile_to_domain(model)

    def update(
        self,
        profile: Profile,
    ) -> None:
        """Persist changes to an existing profile."""

        model = self._session.get(
            ProfileModel,
            profile.id,
        )

        if model is None:
            raise LookupError(
                f"Profile {profile.id} does not exist.",
            )

        model.platform = profile.platform.value
        model.external_id = profile.external_id
        model.username = profile.username
        model.created_at = profile.created_at
        model.updated_at = profile.updated_at
