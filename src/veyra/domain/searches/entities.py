"""Search domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now
from veyra.domain.profiles import SocialPlatform

from .enums import CandidateStatus, SearchStatus

_ALLOWED_SEARCH_TRANSITIONS: dict[
    SearchStatus,
    frozenset[SearchStatus],
] = {
    SearchStatus.CREATED: frozenset(
        {
            SearchStatus.DISCOVERING,
            SearchStatus.FAILED,
        }
    ),
    SearchStatus.DISCOVERING: frozenset(
        {
            SearchStatus.SNAPSHOTTING,
            SearchStatus.FAILED,
        }
    ),
    SearchStatus.SNAPSHOTTING: frozenset(
        {
            SearchStatus.ANALYZING,
            SearchStatus.FAILED,
        }
    ),
    SearchStatus.ANALYZING: frozenset(
        {
            SearchStatus.SCORING,
            SearchStatus.FAILED,
        }
    ),
    SearchStatus.SCORING: frozenset(
        {
            SearchStatus.COMPLETED,
            SearchStatus.FAILED,
        }
    ),
    SearchStatus.COMPLETED: frozenset(),
    SearchStatus.FAILED: frozenset(),
}


@dataclass(slots=True)
class Search:
    """One profile-discovery and analysis execution."""

    platform: SocialPlatform
    id: UUID = field(default_factory=uuid4)
    status: SearchStatus = SearchStatus.CREATED
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        self.created_at = ensure_utc_datetime(self.created_at, field_name="created_at")
        self.updated_at = ensure_utc_datetime(self.updated_at, field_name="updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at.")
        if self.started_at is not None:
            self.started_at = ensure_utc_datetime(self.started_at, field_name="started_at")
            if self.started_at < self.created_at:
                raise ValueError("started_at must not be earlier than created_at.")
        if self.completed_at is not None:
            self.completed_at = ensure_utc_datetime(self.completed_at, field_name="completed_at")
            if self.completed_at < self.created_at:
                raise ValueError("completed_at must not be earlier than created_at.")
            if self.started_at is not None and self.completed_at < self.started_at:
                raise ValueError("completed_at must not be earlier than started_at.")
        if self.failure_reason is not None:
            self.failure_reason = self.failure_reason.strip() or None
        self._validate_state()

    def transition_to(
        self,
        status: SearchStatus,
        *,
        changed_at: datetime | None = None,
    ) -> None:
        if status is SearchStatus.FAILED:
            raise ValueError("Use fail() to transition a search to failed.")
        if status is self.status:
            return
        timestamp = self._prepare_transition(status, changed_at=changed_at)
        if self.status is SearchStatus.CREATED and status is SearchStatus.DISCOVERING:
            self.started_at = timestamp
        if status is SearchStatus.COMPLETED:
            self.completed_at = timestamp
        self.status = status
        self.updated_at = timestamp
        self._validate_state()

    def fail(
        self,
        reason: str,
        *,
        changed_at: datetime | None = None,
    ) -> None:
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError("failure reason must not be empty.")
        timestamp = self._prepare_transition(SearchStatus.FAILED, changed_at=changed_at)
        self.status = SearchStatus.FAILED
        self.failure_reason = normalized_reason
        self.completed_at = timestamp
        self.updated_at = timestamp
        self._validate_state()

    def _prepare_transition(
        self,
        status: SearchStatus,
        *,
        changed_at: datetime | None,
    ) -> datetime:
        allowed_statuses = _ALLOWED_SEARCH_TRANSITIONS[self.status]
        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid search transition: {self.status.value} -> {status.value}.",
            )
        timestamp = ensure_utc_datetime(
            changed_at or utc_now(),
            field_name="changed_at",
        )
        if timestamp < self.updated_at:
            raise ValueError("changed_at must not be earlier than updated_at.")
        return timestamp

    def _validate_state(self) -> None:
        if self.status is SearchStatus.CREATED:
            if self.started_at is not None:
                raise ValueError("created search must not have started_at.")
            if self.completed_at is not None:
                raise ValueError("created search must not have completed_at.")
            if self.failure_reason is not None:
                raise ValueError("created search must not have failure_reason.")
            return

        if self.status in {
            SearchStatus.DISCOVERING,
            SearchStatus.SNAPSHOTTING,
            SearchStatus.ANALYZING,
            SearchStatus.SCORING,
        }:
            if self.started_at is None:
                raise ValueError("active search must have started_at.")
            if self.completed_at is not None:
                raise ValueError("active search must not have completed_at.")
            if self.failure_reason is not None:
                raise ValueError("active search must not have failure_reason.")
            return

        if self.status is SearchStatus.COMPLETED:
            if self.started_at is None:
                raise ValueError("completed search must have started_at.")
            if self.completed_at is None:
                raise ValueError("completed search must have completed_at.")
            if self.failure_reason is not None:
                raise ValueError("completed search must not have failure_reason.")
            return

        if self.status is SearchStatus.FAILED:
            if self.completed_at is None:
                raise ValueError("failed search must have completed_at.")
            if self.failure_reason is None:
                raise ValueError("failed search must have failure_reason.")


@dataclass(slots=True)
class SearchCandidate:
    """Association between a Search and a discovered Profile."""

    search_id: UUID
    profile_id: UUID
    discovery_source: str
    id: UUID = field(default_factory=uuid4)
    status: CandidateStatus = CandidateStatus.DISCOVERED
    discovered_at: datetime = field(default_factory=utc_now)
    snapshot_id: UUID | None = None
    score: float | None = None
    exclusion_reason: str | None = None

    def __post_init__(self) -> None:
        self.discovery_source = self.discovery_source.strip()
        if not self.discovery_source:
            raise ValueError("discovery_source must not be empty.")
        self.discovered_at = ensure_utc_datetime(
            self.discovered_at,
            field_name="discovered_at",
        )
        self._validate_score(self.score)
        if self.exclusion_reason is not None:
            self.exclusion_reason = self.exclusion_reason.strip() or None
        self._validate_state()

    def attach_snapshot(
        self,
        snapshot_id: UUID,
    ) -> None:
        if self.status is not CandidateStatus.DISCOVERED:
            raise ValueError(
                "Snapshot can only be attached to a discovered candidate.",
            )
        self.snapshot_id = snapshot_id
        self.status = CandidateStatus.SNAPSHOTTED
        self._validate_state()

    def mark_analyzed(self) -> None:
        if self.status is not CandidateStatus.SNAPSHOTTED:
            raise ValueError(
                "Only snapshotted candidates can be marked analyzed.",
            )
        self.status = CandidateStatus.ANALYZED
        self._validate_state()

    def filter_out(
        self,
        reason: str,
    ) -> None:
        """Exclude a snapshotted or analyzed candidate from further processing."""

        if self.status not in {
            CandidateStatus.SNAPSHOTTED,
            CandidateStatus.ANALYZED,
        }:
            raise ValueError(
                "Only snapshotted or analyzed candidates can be filtered out.",
            )

        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError(
                "exclusion reason must not be empty.",
            )

        self.exclusion_reason = normalized_reason
        self.score = None
        self.status = CandidateStatus.FILTERED_OUT
        self._validate_state()

    def set_score(
        self,
        score: float,
    ) -> None:
        if self.status is not CandidateStatus.ANALYZED:
            raise ValueError(
                "Only analyzed candidates can be scored.",
            )
        self._validate_score(score)
        self.score = float(score)
        self.exclusion_reason = None
        self.status = CandidateStatus.SCORED
        self._validate_state()

    def _validate_state(self) -> None:
        if self.status is CandidateStatus.DISCOVERED:
            if self.snapshot_id is not None:
                raise ValueError("discovered candidate must not have snapshot_id.")
            if self.score is not None:
                raise ValueError("discovered candidate must not have score.")
            if self.exclusion_reason is not None:
                raise ValueError("discovered candidate must not have exclusion_reason.")
            return

        if self.snapshot_id is None:
            raise ValueError("processed candidate must have snapshot_id.")

        if self.status in {
            CandidateStatus.SNAPSHOTTED,
            CandidateStatus.ANALYZED,
        }:
            if self.score is not None:
                raise ValueError("unscored candidate must not have score.")
            if self.exclusion_reason is not None:
                raise ValueError("unfiltered candidate must not have exclusion_reason.")
            return

        if self.status is CandidateStatus.FILTERED_OUT:
            if self.score is not None:
                raise ValueError("filtered candidate must not have score.")
            if self.exclusion_reason is None:
                raise ValueError("filtered candidate must have exclusion_reason.")
            return

        if self.status is CandidateStatus.SCORED:
            if self.score is None:
                raise ValueError("scored candidate must have score.")
            if self.exclusion_reason is not None:
                raise ValueError("scored candidate must not have exclusion_reason.")

    @staticmethod
    def _validate_score(
        score: float | None,
    ) -> None:
        if score is None:
            return
        if isinstance(score, bool):
            raise ValueError(
                "score must be a numeric value between 0 and 10.",
            )
        if not 0 <= score <= 10:
            raise ValueError(
                "score must be between 0 and 10.",
            )
