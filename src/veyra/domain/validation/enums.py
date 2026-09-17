"""Validation domain enumerations."""

from enum import StrEnum


class ValidationCode(StrEnum):
    """Machine-readable validation result codes."""

    VALID = "valid"

    AGE_CONFIRMED_ADULT = "age_confirmed_adult"
    AGE_UNCERTAIN = "age_uncertain"
    POSSIBLE_MINOR = "possible_minor"

    LOCATION_CONFIRMED = "location_confirmed"
    LOCATION_UNCERTAIN = "location_uncertain"

    PROFILE_INCOMPLETE = "profile_incomplete"
    PROFILE_SUSPICIOUS = "profile_suspicious"

    CONFLICTING_EVIDENCE = "conflicting_evidence"


class ValidationSeverity(StrEnum):
    """Severity of a validation finding."""

    INFO = "info"
    WARNING = "warning"
    REJECT = "reject"
