"""Profile domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now

from .enums import SocialPlatform


@dataclass(slots=True)
class Profile:
    """
    Persistent identity of a discovered social profile.

    A Profile represents the account itself. Historical mutable profile
    attributes belong to ProfileSnapshot instead.
    """

    platform: SocialPlatform
    external_id: str
    username: str

    id: UUID = field(
        default_factory=uuid4,
    )

    created_at: datetime = field(
        default_factory=utc_now,
    )

    updated_at: datetime = field(
        default_factory=utc_now,
    )

    def __post_init__(self) -> None:
        """Validate and normalize profile state."""

        self.external_id = self.external_id.strip()
        self.username = self._normalize_username(self.username)

        if not self.external_id:
            raise ValueError(
                "external_id must not be empty.",
            )

        if not self.username:
            raise ValueError(
                "username must not be empty.",
            )

        self.created_at = ensure_utc_datetime(
            self.created_at,
            field_name="created_at",
        )

        self.updated_at = ensure_utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at must not be earlier than created_at.",
            )

    def change_username(
        self,
        username: str,
        *,
        changed_at: datetime | None = None,
    ) -> None:
        """Update the profile's current username."""

        normalized_username = self._normalize_username(
            username,
        )

        if not normalized_username:
            raise ValueError(
                "username must not be empty.",
            )

        timestamp = ensure_utc_datetime(
            changed_at or utc_now(),
            field_name="changed_at",
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "changed_at must not be earlier than updated_at.",
            )

        self.username = normalized_username
        self.updated_at = timestamp

    @staticmethod
    def _normalize_username(
        username: str,
    ) -> str:
        """Normalize a social username representation."""

        return username.strip().removeprefix("@").strip()
