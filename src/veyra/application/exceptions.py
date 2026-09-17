"""Application layer exceptions."""

from uuid import UUID


class ApplicationError(Exception):
    """Base exception for application use-case failures."""


class EntityNotFoundError(ApplicationError):
    """Raised when an application use case cannot locate an entity."""

    def __init__(
        self,
        entity_name: str,
        entity_id: UUID,
    ) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id

        super().__init__(
            f"{entity_name} {entity_id} was not found.",
        )


class ProfileAlreadyExistsError(ApplicationError):
    """Raised when a social profile identity already exists."""

    def __init__(
        self,
        *,
        platform: str,
        external_id: str,
    ) -> None:
        self.platform = platform
        self.external_id = external_id

        super().__init__(
            f"Profile already exists for {platform}:{external_id}.",
        )


class CandidateAlreadyExistsError(ApplicationError):
    """Raised when a profile is already attached to a search."""

    def __init__(
        self,
        *,
        search_id: UUID,
        profile_id: UUID,
    ) -> None:
        self.search_id = search_id
        self.profile_id = profile_id

        super().__init__(
            f"Profile {profile_id} is already a candidate of search {search_id}.",
        )
