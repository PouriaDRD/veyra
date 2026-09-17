"""Evidence domain enumerations."""

from enum import StrEnum


class EvidenceSource(StrEnum):
    """Origin of extracted evidence."""

    USERNAME = "username"
    BIO = "bio"
    DISPLAY_NAME = "display_name"
    PROFILE_METADATA = "profile_metadata"
    PUBLIC_CONTENT = "public_content"
    PROVIDER_METADATA = "provider_metadata"


class FactKind(StrEnum):
    """Supported normalized fact categories."""

    BIRTH_YEAR = "birth_year"
    AGE = "age"
    LOCATION = "location"
    PROFILE_TYPE = "profile_type"
    ACCOUNT_ACTIVITY = "account_activity"
    FOLLOWER_COUNT = "follower_count"


class FactStatus(StrEnum):
    """Resolution status of one normalized fact."""

    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"


class ConfidenceLevel(StrEnum):
    """Human-readable confidence band."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
