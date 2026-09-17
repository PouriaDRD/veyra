"""Media domain enumerations."""

from enum import StrEnum


class MediaKind(StrEnum):
    """Stored media content kind."""

    IMAGE = "image"
    VIDEO = "video"


class SnapshotMediaRole(StrEnum):
    """Role of a media asset within one profile snapshot."""

    PROFILE_PICTURE = "profile_picture"
    IMAGE = "image"
    VIDEO = "video"
    THUMBNAIL = "thumbnail"
