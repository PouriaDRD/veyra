"""Search application data-transfer objects."""

from dataclasses import dataclass
from uuid import UUID

from veyra.domain.profiles import SocialPlatform


@dataclass(frozen=True, slots=True)
class CreateSearchCommand:
    """Input required to create a new search."""

    platform: SocialPlatform


@dataclass(frozen=True, slots=True)
class AddCandidateCommand:
    """Input required to attach a profile to a search."""

    search_id: UUID
    profile_id: UUID
    discovery_source: str


@dataclass(frozen=True, slots=True)
class CaptureSnapshotCommand:
    """Input required to capture one profile observation."""

    profile_id: UUID
    username: str

    display_name: str | None = None
    bio: str | None = None

    followers_count: int | None = None
    following_count: int | None = None
    posts_count: int | None = None

    is_private: bool | None = None
    is_verified: bool | None = None

    profile_picture_url: str | None = None
