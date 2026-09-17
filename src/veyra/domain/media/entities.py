"""Media domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now

from .enums import MediaKind


@dataclass(slots=True)
class MediaAsset:
    """
    Locally persisted media asset.

    SHA-256 acts as the content identity used for deduplication.
    """

    sha256: str
    kind: MediaKind
    mime_type: str
    extension: str
    byte_size: int
    storage_path: Path

    original_url: str | None = None

    width: int | None = None
    height: int | None = None

    id: UUID = field(
        default_factory=uuid4,
    )

    downloaded_at: datetime = field(
        default_factory=utc_now,
    )

    def __post_init__(self) -> None:
        """Validate and normalize media metadata."""

        self.sha256 = self.sha256.strip().lower()

        if len(self.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256
        ):
            raise ValueError(
                "sha256 must be a 64-character hexadecimal digest.",
            )

        self.mime_type = self.mime_type.strip().lower()

        if not self.mime_type:
            raise ValueError(
                "mime_type must not be empty.",
            )

        self.extension = self.extension.strip().lower().removeprefix(".")

        if not self.extension:
            raise ValueError(
                "extension must not be empty.",
            )

        if self.byte_size <= 0:
            raise ValueError(
                "byte_size must be greater than zero.",
            )

        if not str(self.storage_path).strip():
            raise ValueError(
                "storage_path must not be empty.",
            )

        if (self.width is None) != (self.height is None):
            raise ValueError(
                "width and height must either both be set or both be None.",
            )

        if self.width is not None and self.width <= 0:
            raise ValueError(
                "width must be greater than zero.",
            )

        if self.height is not None and self.height <= 0:
            raise ValueError(
                "height must be greater than zero.",
            )

        if self.original_url is not None:
            self.original_url = self.original_url.strip() or None

        self.downloaded_at = ensure_utc_datetime(
            self.downloaded_at,
            field_name="downloaded_at",
        )
