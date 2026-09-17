"""Search application services."""

from uuid import UUID

from veyra.application.dto import (
    AddCandidateCommand,
    CaptureSnapshotCommand,
    CreateSearchCommand,
)
from veyra.application.dto.analysis import ProfileAnalysisResult
from veyra.application.exceptions import (
    CandidateAlreadyExistsError,
    EntityNotFoundError,
)
from veyra.application.ports import UnitOfWork
from veyra.application.scoring import (
    AnalysisScoringPolicy,
    CandidateScoringResult,
    ProfileScoringService,
)
from veyra.domain.scoring import ScoreSnapshot
from veyra.domain.searches import (
    CandidateStatus,
    Search,
    SearchCandidate,
    SearchStatus,
)
from veyra.domain.snapshots import ProfileSnapshot

PUBLIC_PROFILE_EXCLUSION_REASON = "Public profiles are not eligible for scoring."
UNKNOWN_PRIVACY_SCORING_ERROR = "Candidate privacy must be confirmed private before scoring."


class SearchService:
    """Application use cases for search execution."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        *,
        profile_scoring_service: ProfileScoringService | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._profile_scoring_service = (
            profile_scoring_service
            if profile_scoring_service is not None
            else ProfileScoringService()
        )

    def create(self, command: CreateSearchCommand) -> Search:
        search = Search(platform=command.platform)
        with self._unit_of_work as unit_of_work:
            unit_of_work.searches.add(search)
        return search

    def start(self, search_id: UUID) -> Search:
        with self._unit_of_work as unit_of_work:
            search = self._get_search(unit_of_work, search_id)
            search.transition_to(SearchStatus.DISCOVERING)
            unit_of_work.searches.update(search)
            return search

    def add_candidate(self, command: AddCandidateCommand) -> SearchCandidate:
        with self._unit_of_work as unit_of_work:
            self._get_search(unit_of_work, command.search_id)
            profile = unit_of_work.profiles.get_by_id(command.profile_id)
            if profile is None:
                raise EntityNotFoundError("Profile", command.profile_id)
            existing = unit_of_work.candidates.get_by_search_and_profile(
                command.search_id,
                command.profile_id,
            )
            if existing is not None:
                raise CandidateAlreadyExistsError(
                    search_id=command.search_id,
                    profile_id=command.profile_id,
                )
            candidate = SearchCandidate(
                search_id=command.search_id,
                profile_id=command.profile_id,
                discovery_source=command.discovery_source,
            )
            unit_of_work.candidates.add(candidate)
            return candidate

    def capture_snapshot(
        self,
        candidate_id: UUID,
        command: CaptureSnapshotCommand,
    ) -> ProfileSnapshot:
        """Capture profile state and immediately exclude confirmed-public profiles."""

        with self._unit_of_work as unit_of_work:
            candidate = self._get_candidate(unit_of_work, candidate_id)

            if candidate.profile_id != command.profile_id:
                raise ValueError(
                    "Snapshot profile does not match candidate profile.",
                )

            profile = unit_of_work.profiles.get_by_id(command.profile_id)
            if profile is None:
                raise EntityNotFoundError("Profile", command.profile_id)

            snapshot = ProfileSnapshot(
                profile_id=command.profile_id,
                username=command.username,
                display_name=command.display_name,
                bio=command.bio,
                followers_count=command.followers_count,
                following_count=command.following_count,
                posts_count=command.posts_count,
                is_private=command.is_private,
                is_verified=command.is_verified,
                profile_picture_url=command.profile_picture_url,
            )

            unit_of_work.snapshots.add(snapshot)
            candidate.attach_snapshot(snapshot.id)

            if snapshot.is_private is False:
                candidate.filter_out(
                    PUBLIC_PROFILE_EXCLUSION_REASON,
                )

            unit_of_work.candidates.update(candidate)
            return snapshot

    def mark_candidate_analyzed(self, candidate_id: UUID) -> SearchCandidate:
        with self._unit_of_work as unit_of_work:
            candidate = self._get_candidate(unit_of_work, candidate_id)
            candidate.mark_analyzed()
            unit_of_work.candidates.update(candidate)
            return candidate

    def score_candidate(
        self,
        candidate_id: UUID,
        score: float,
    ) -> SearchCandidate:
        """Assign an already-computed score only to confirmed-private candidates."""

        with self._unit_of_work as unit_of_work:
            candidate = self._get_candidate(unit_of_work, candidate_id)
            snapshot = self._get_candidate_snapshot(
                unit_of_work,
                candidate,
            )

            if snapshot.is_private is False:
                if candidate.status in {
                    CandidateStatus.SNAPSHOTTED,
                    CandidateStatus.ANALYZED,
                }:
                    candidate.filter_out(
                        PUBLIC_PROFILE_EXCLUSION_REASON,
                    )
                    unit_of_work.candidates.update(candidate)
                return candidate

            if snapshot.is_private is not True:
                raise ValueError(
                    UNKNOWN_PRIVACY_SCORING_ERROR,
                )

            candidate.set_score(score)
            unit_of_work.candidates.update(candidate)
            return candidate

    def score_candidate_from_analysis(
        self,
        candidate_id: UUID,
        analysis: ProfileAnalysisResult,
        policy: AnalysisScoringPolicy,
    ) -> CandidateScoringResult:
        """
        Score only a confirmed-private analyzed candidate.

        Public candidates are excluded. Unknown privacy stays unscorable.
        Successful score persistence and audit insertion remain atomic.
        """

        with self._unit_of_work as unit_of_work:
            candidate = self._get_candidate(unit_of_work, candidate_id)
            snapshot = self._get_candidate_snapshot(
                unit_of_work,
                candidate,
            )

            self._validate_analysis_matches_candidate(
                candidate,
                analysis,
            )

            if analysis.is_private is not snapshot.is_private:
                raise ValueError(
                    "Analysis privacy state does not match candidate snapshot.",
                )

            score_result = self._profile_scoring_service.score(
                analysis,
                policy,
            )

            if snapshot.is_private is False:
                if candidate.status in {
                    CandidateStatus.SNAPSHOTTED,
                    CandidateStatus.ANALYZED,
                }:
                    candidate.filter_out(
                        PUBLIC_PROFILE_EXCLUSION_REASON,
                    )
                    unit_of_work.candidates.update(candidate)

                return CandidateScoringResult(
                    candidate=candidate,
                    score_result=score_result,
                    persisted=False,
                    audit_snapshot=None,
                )

            if score_result.score is None:
                return CandidateScoringResult(
                    candidate=candidate,
                    score_result=score_result,
                    persisted=False,
                    audit_snapshot=None,
                )

            candidate.set_score(score_result.score)

            audit_snapshot = ScoreSnapshot.from_result(
                candidate_id=candidate.id,
                profile_snapshot_id=analysis.snapshot_id,
                result=score_result,
            )

            unit_of_work.candidates.update(candidate)
            unit_of_work.score_snapshots.add(audit_snapshot)

            return CandidateScoringResult(
                candidate=candidate,
                score_result=score_result,
                persisted=True,
                audit_snapshot=audit_snapshot,
            )

    def filter_candidate(
        self,
        candidate_id: UUID,
        reason: str,
    ) -> SearchCandidate:
        with self._unit_of_work as unit_of_work:
            candidate = self._get_candidate(unit_of_work, candidate_id)
            candidate.filter_out(reason)
            unit_of_work.candidates.update(candidate)
            return candidate

    @staticmethod
    def _validate_analysis_matches_candidate(
        candidate: SearchCandidate,
        analysis: ProfileAnalysisResult,
    ) -> None:
        if candidate.profile_id != analysis.profile_id:
            raise ValueError(
                "Analysis profile does not match candidate profile.",
            )
        if candidate.snapshot_id != analysis.snapshot_id:
            raise ValueError(
                "Analysis snapshot does not match candidate snapshot.",
            )

    @staticmethod
    def _get_candidate_snapshot(
        unit_of_work: UnitOfWork,
        candidate: SearchCandidate,
    ) -> ProfileSnapshot:
        if candidate.snapshot_id is None:
            raise ValueError(
                "Candidate must have a snapshot before scoring.",
            )

        snapshot = unit_of_work.snapshots.get_by_id(
            candidate.snapshot_id,
        )
        if snapshot is None:
            raise EntityNotFoundError(
                "ProfileSnapshot",
                candidate.snapshot_id,
            )
        return snapshot

    @staticmethod
    def _get_search(
        unit_of_work: UnitOfWork,
        search_id: UUID,
    ) -> Search:
        search = unit_of_work.searches.get_by_id(search_id)
        if search is None:
            raise EntityNotFoundError("Search", search_id)
        return search

    @staticmethod
    def _get_candidate(
        unit_of_work: UnitOfWork,
        candidate_id: UUID,
    ) -> SearchCandidate:
        candidate = unit_of_work.candidates.get_by_id(candidate_id)
        if candidate is None:
            raise EntityNotFoundError("SearchCandidate", candidate_id)
        return candidate
