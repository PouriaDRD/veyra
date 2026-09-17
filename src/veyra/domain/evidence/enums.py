"""Evidence domain enumerations."""

from enum import StrEnum


class EvidenceSource(StrEnum):
    """Origin of extracted evidence."""

    USERNAME = "username"
    BIO = "bio"
    DISPLAY_NAME = "display_name"

    PROFILE_METADATA = "profile_metadata"

    PUBLIC_CONTENT = "public_content"
    CAPTION = "caption"
    HASHTAG = "hashtag"
    MENTION = "mention"
    GEOTAG = "geotag"

    EXTERNAL_LINK = "external_link"

    PROVIDER_METADATA = "provider_metadata"


class DeclaredGender(StrEnum):
    """
    Explicit self-declared gender values supported by candidate eligibility.

    This value describes explicit evidence only. It is not populated from
    names, usernames, photos, clothing, emoji, or other proxy attributes.
    """

    FEMALE = "female"
    MALE = "male"


class FactKind(StrEnum):
    """Supported normalized factual categories."""

    USERNAME = "username"
    DISPLAY_NAME = "display_name"

    BIRTH_YEAR = "birth_year"
    AGE = "age"
    DECLARED_GENDER = "declared_gender"

    LOCATION = "location"
    COUNTRY = "country"
    CITY = "city"

    OCCUPATION = "occupation"
    EMPLOYER = "employer"

    EDUCATION = "education"
    INSTITUTION = "institution"

    LANGUAGE = "language"

    RELATIONSHIP_STATUS = "relationship_status"

    PROFILE_TYPE = "profile_type"

    FOLLOWER_COUNT = "follower_count"
    FOLLOWING_COUNT = "following_count"
    POST_COUNT = "post_count"

    ACCOUNT_ACTIVITY = "account_activity"

    EXTERNAL_LINK = "external_link"
    CONTACT_EMAIL = "contact_email"
    CONTACT_PHONE = "contact_phone"

    CONTENT_TOPIC = "content_topic"


class FactStatus(StrEnum):
    """Resolution status of one normalized fact."""

    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"


class FactCardinality(StrEnum):
    """Whether one fact kind resolves to one value or multiple values."""

    SINGLE = "single"
    MULTIPLE = "multiple"


class ConfidenceLevel(StrEnum):
    """Human-readable confidence band."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
