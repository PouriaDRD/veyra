"""Profile snapshot domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now


@dataclass(slots=True)
class ProfileSnapshot:
    """
    Immutable-in-time observation of a social profile.

    A new snapshot should be created whenever Veyra captures fresh profile
    state instead of overwriting historical information.
    """

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

    id: UUID = field(
        default_factory=uuid4,
    )

    captured_at: datetime = field(
        default_factory=utc_now,
    )

    def __post_init__(self) -> None:
        """Validate and normalize snapshot data."""

        self.username = self.username.strip().removeprefix("@").strip()

        if not self.username:
            raise ValueError(
                "username must not be empty.",
            )

        self.display_name = self._normalize_optional_text(
            self.display_name,
        )

        self.bio = self._normalize_optional_text(
            self.bio,
        )

        self.profile_picture_url = self._normalize_optional_text(
            self.profile_picture_url,
        )

        self._validate_optional_count(
            self.followers_count,
            field_name="followers_count",
        )

        self._validate_optional_count(
            self.following_count,
            field_name="following_count",
        )

        self._validate_optional_count(
            self.posts_count,
            field_name="posts_count",
        )

        self.captured_at = ensure_utc_datetime(
            self.captured_at,
            field_name="captured_at",
        )

    @staticmethod
    def _validate_optional_count(
        value: int | None,
        *,
        field_name: str,
    ) -> None:
        """Validate an optional non-negative count."""

        if value is not None and value < 0:
            raise ValueError(
                f"{field_name} must not be negative.",
            )

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        """Normalize optional textual snapshot fields."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None
