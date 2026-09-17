"""Search domain enumerations."""

from enum import StrEnum


class SearchStatus(StrEnum):
    """Lifecycle status of a Veyra search."""

    CREATED = "created"
    DISCOVERING = "discovering"
    SNAPSHOTTING = "snapshotting"
    ANALYZING = "analyzing"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


class CandidateStatus(StrEnum):
    """Processing status of a discovered search candidate."""

    DISCOVERED = "discovered"
    SNAPSHOTTED = "snapshotted"
    ANALYZED = "analyzed"
    FILTERED_OUT = "filtered_out"
    SCORED = "scored"
