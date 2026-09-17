"""General profile-intelligence taxonomy."""

from enum import StrEnum


class EvidenceNature(StrEnum):
    """Semantic nature of one piece of evidence."""

    EXPLICIT = "explicit"
    OBSERVED = "observed"
    CONTEXTUAL = "contextual"
    DERIVED = "derived"
    AMBIGUOUS = "ambiguous"


class EvidenceStrength(StrEnum):
    """Qualitative semantic strength of one observation."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class IntelligenceCategory(StrEnum):
    """Top-level profile-intelligence categories."""

    IDENTITY = "identity"
    DEMOGRAPHIC = "demographic"
    LOCATION = "location"
    PROFESSIONAL = "professional"
    EDUCATION = "education"
    RELATIONSHIP = "relationship"
    PROFILE = "profile"
    AUDIENCE = "audience"
    ACTIVITY = "activity"
    CONTENT = "content"
    CONTACT = "contact"
    TEMPORAL = "temporal"


class HypothesisKind(StrEnum):
    """Supported derived hypotheses."""

    RELATIONSHIP_STATUS = "relationship_status"
    LIKELY_LOCATION = "likely_location"
    PROFILE_PURPOSE = "profile_purpose"
    ACTIVITY_LEVEL = "activity_level"
    CONTENT_INTEREST = "content_interest"


class HypothesisStatus(StrEnum):
    """Resolution state of one derived hypothesis."""

    UNKNOWN = "unknown"
    POSSIBLE = "possible"
    PROBABLE = "probable"
    STRONGLY_SUPPORTED = "strongly_supported"
    AMBIGUOUS = "ambiguous"
    CONFLICTED = "conflicted"


class RelationshipStatus(StrEnum):
    """Normalized explicit public relationship-status claim."""

    SINGLE = "single"
    MARRIED = "married"
    ENGAGED = "engaged"
    IN_RELATIONSHIP = "in_relationship"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    UNKNOWN = "unknown"


class RelationshipSignalKind(StrEnum):
    """
    Contextual relationship-themed signals.

    These signals are not relationship-status facts.
    """

    RING_EMOJI = "ring_emoji"
    RED_HEART_EMOJI = "red_heart_emoji"
    HEART_EMOJI = "heart_emoji"
    NAME_ADJACENT_HEART = "name_adjacent_heart"
    NAME_ADJACENT_RING = "name_adjacent_ring"


class ProfilePurpose(StrEnum):
    """High-level public profile purpose."""

    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    CREATOR = "creator"
    BUSINESS = "business"
    ORGANIZATION = "organization"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ActivityLevel(StrEnum):
    """Normalized account activity level."""

    INACTIVE = "inactive"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"
