"""Repository contracts used by the application layer."""

from typing import Protocol
from uuid import UUID

from veyra.domain.media import MediaAsset
from veyra.domain.profiles import Profile, SocialPlatform
from veyra.domain.searches import Search, SearchCandidate
from veyra.domain.snapshots import ProfileSnapshot


class ProfileRepository(Protocol):
    """Persistence contract for Profile entities."""

    def add(
        self,
        profile: Profile,
    ) -> None:
        """Persist a new profile."""
        ...

    def get_by_id(
        self,
        profile_id: UUID,
    ) -> Profile | None:
        """Return a profile by identifier."""
        ...

    def get_by_external_identity(
        self,
        platform: SocialPlatform,
        external_id: str,
    ) -> Profile | None:
        """Return a profile by platform and external identifier."""
        ...

    def get_by_username(
        self,
        platform: SocialPlatform,
        username: str,
    ) -> Profile | None:
        """Return a profile by platform and username."""
        ...

    def update(
        self,
        profile: Profile,
    ) -> None:
        """Persist changes to an existing profile."""
        ...


class SnapshotRepository(Protocol):
    """Persistence contract for ProfileSnapshot entities."""

    def add(
        self,
        snapshot: ProfileSnapshot,
    ) -> None:
        """Persist a profile snapshot."""
        ...

    def get_by_id(
        self,
        snapshot_id: UUID,
    ) -> ProfileSnapshot | None:
        """Return a snapshot by identifier."""
        ...

    def list_for_profile(
        self,
        profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[ProfileSnapshot]:
        """Return snapshots for a profile, newest first."""
        ...


class SearchRepository(Protocol):
    """Persistence contract for Search entities."""

    def add(
        self,
        search: Search,
    ) -> None:
        """Persist a new search."""
        ...

    def get_by_id(
        self,
        search_id: UUID,
    ) -> Search | None:
        """Return a search by identifier."""
        ...

    def update(
        self,
        search: Search,
    ) -> None:
        """Persist changes to an existing search."""
        ...


class SearchCandidateRepository(Protocol):
    """Persistence contract for SearchCandidate entities."""

    def add(
        self,
        candidate: SearchCandidate,
    ) -> None:
        """Persist a search candidate."""
        ...

    def get_by_id(
        self,
        candidate_id: UUID,
    ) -> SearchCandidate | None:
        """Return a candidate by identifier."""
        ...

    def get_by_search_and_profile(
        self,
        search_id: UUID,
        profile_id: UUID,
    ) -> SearchCandidate | None:
        """Return the candidate for one search/profile pair."""
        ...

    def list_for_search(
        self,
        search_id: UUID,
    ) -> list[SearchCandidate]:
        """Return candidates belonging to one search."""
        ...

    def update(
        self,
        candidate: SearchCandidate,
    ) -> None:
        """Persist changes to an existing candidate."""
        ...


class MediaAssetRepository(Protocol):
    """Persistence contract for MediaAsset entities."""

    def add(
        self,
        asset: MediaAsset,
    ) -> None:
        """Persist a media asset."""
        ...

    def get_by_id(
        self,
        asset_id: UUID,
    ) -> MediaAsset | None:
        """Return a media asset by identifier."""
        ...

    def get_by_sha256(
        self,
        sha256: str,
    ) -> MediaAsset | None:
        """Return a media asset by content digest."""
        ...

    def get_by_storage_path(
        self,
        storage_path: str,
    ) -> MediaAsset | None:
        """Return a media asset by local storage path."""
        ...
