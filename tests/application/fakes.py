"""In-memory fakes for application service tests."""

from copy import deepcopy
from types import TracebackType
from uuid import UUID

from veyra.domain.media import MediaAsset
from veyra.domain.profiles import Profile, SocialPlatform
from veyra.domain.scoring import ScoreSnapshot
from veyra.domain.searches import Search, SearchCandidate
from veyra.domain.snapshots import ProfileSnapshot


class FakeProfileRepository:
    """In-memory profile repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, Profile] = {}

    def add(
        self,
        profile: Profile,
    ) -> None:
        self.items[profile.id] = profile

    def get_by_id(
        self,
        profile_id: UUID,
    ) -> Profile | None:
        return self.items.get(profile_id)

    def get_by_external_identity(
        self,
        platform: SocialPlatform,
        external_id: str,
    ) -> Profile | None:
        for profile in self.items.values():
            if profile.platform is platform and profile.external_id == external_id:
                return profile

        return None

    def get_by_username(
        self,
        platform: SocialPlatform,
        username: str,
    ) -> Profile | None:
        normalized = username.strip().removeprefix("@").strip()

        for profile in self.items.values():
            if profile.platform is platform and profile.username == normalized:
                return profile

        return None

    def update(
        self,
        profile: Profile,
    ) -> None:
        if profile.id not in self.items:
            raise LookupError(
                f"Profile {profile.id} does not exist.",
            )

        self.items[profile.id] = profile


class FakeSnapshotRepository:
    """In-memory snapshot repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, ProfileSnapshot] = {}

    def add(
        self,
        snapshot: ProfileSnapshot,
    ) -> None:
        self.items[snapshot.id] = snapshot

    def get_by_id(
        self,
        snapshot_id: UUID,
    ) -> ProfileSnapshot | None:
        return self.items.get(snapshot_id)

    def list_for_profile(
        self,
        profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[ProfileSnapshot]:
        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be greater than zero.",
            )

        snapshots = [
            snapshot for snapshot in self.items.values() if snapshot.profile_id == profile_id
        ]

        snapshots.sort(
            key=lambda snapshot: snapshot.captured_at,
            reverse=True,
        )

        if limit is not None:
            snapshots = snapshots[:limit]

        return snapshots


class FakeSearchRepository:
    """In-memory search repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, Search] = {}

    def add(
        self,
        search: Search,
    ) -> None:
        self.items[search.id] = search

    def get_by_id(
        self,
        search_id: UUID,
    ) -> Search | None:
        return self.items.get(search_id)

    def update(
        self,
        search: Search,
    ) -> None:
        if search.id not in self.items:
            raise LookupError(
                f"Search {search.id} does not exist.",
            )

        self.items[search.id] = search


class FakeCandidateRepository:
    """In-memory candidate repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, SearchCandidate] = {}

    def add(
        self,
        candidate: SearchCandidate,
    ) -> None:
        self.items[candidate.id] = candidate

    def get_by_id(
        self,
        candidate_id: UUID,
    ) -> SearchCandidate | None:
        return self.items.get(candidate_id)

    def get_by_search_and_profile(
        self,
        search_id: UUID,
        profile_id: UUID,
    ) -> SearchCandidate | None:
        for candidate in self.items.values():
            if candidate.search_id == search_id and candidate.profile_id == profile_id:
                return candidate

        return None

    def list_for_search(
        self,
        search_id: UUID,
    ) -> list[SearchCandidate]:
        return [candidate for candidate in self.items.values() if candidate.search_id == search_id]

    def update(
        self,
        candidate: SearchCandidate,
    ) -> None:
        if candidate.id not in self.items:
            raise LookupError(
                f"SearchCandidate {candidate.id} does not exist.",
            )

        self.items[candidate.id] = candidate


class FakeScoreSnapshotRepository:
    """In-memory append-only score snapshot repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, ScoreSnapshot] = {}

    def add(
        self,
        snapshot: ScoreSnapshot,
    ) -> None:
        if snapshot.id in self.items:
            raise ValueError(
                f"ScoreSnapshot {snapshot.id} already exists.",
            )

        self.items[snapshot.id] = snapshot

    def get_by_id(
        self,
        snapshot_id: UUID,
    ) -> ScoreSnapshot | None:
        return self.items.get(snapshot_id)

    def list_for_candidate(
        self,
        candidate_id: UUID,
    ) -> list[ScoreSnapshot]:
        snapshots = [
            snapshot for snapshot in self.items.values() if snapshot.candidate_id == candidate_id
        ]

        snapshots.sort(
            key=lambda snapshot: (
                snapshot.created_at,
                snapshot.id,
            ),
            reverse=True,
        )

        return snapshots


class FakeMediaAssetRepository:
    """In-memory media repository."""

    def __init__(self) -> None:
        self.items: dict[UUID, MediaAsset] = {}

    def add(
        self,
        asset: MediaAsset,
    ) -> None:
        self.items[asset.id] = asset

    def get_by_id(
        self,
        asset_id: UUID,
    ) -> MediaAsset | None:
        return self.items.get(asset_id)

    def get_by_sha256(
        self,
        sha256: str,
    ) -> MediaAsset | None:
        normalized = sha256.strip().lower()

        for asset in self.items.values():
            if asset.sha256 == normalized:
                return asset

        return None

    def get_by_storage_path(
        self,
        storage_path: str,
    ) -> MediaAsset | None:
        for asset in self.items.values():
            if str(asset.storage_path) == storage_path:
                return asset

        return None


class FakeUnitOfWork:
    """
    In-memory Unit of Work used by application tests.

    Repository state is snapshotted when a transaction begins and restored
    on rollback so behavior mirrors the real transactional Unit of Work.
    """

    def __init__(self) -> None:
        self.profiles = FakeProfileRepository()
        self.snapshots = FakeSnapshotRepository()
        self.searches = FakeSearchRepository()
        self.candidates = FakeCandidateRepository()
        self.score_snapshots = FakeScoreSnapshotRepository()
        self.media_assets = FakeMediaAssetRepository()

        self.commit_count = 0
        self.rollback_count = 0

        self._transaction_snapshot: (
            tuple[
                dict[UUID, Profile],
                dict[UUID, ProfileSnapshot],
                dict[UUID, Search],
                dict[UUID, SearchCandidate],
                dict[UUID, ScoreSnapshot],
                dict[UUID, MediaAsset],
            ]
            | None
        ) = None

    def __enter__(self) -> "FakeUnitOfWork":
        if self._transaction_snapshot is not None:
            raise RuntimeError(
                "Fake Unit of Work is already active.",
            )

        self._transaction_snapshot = (
            deepcopy(self.profiles.items),
            deepcopy(self.snapshots.items),
            deepcopy(self.searches.items),
            deepcopy(self.candidates.items),
            deepcopy(self.score_snapshots.items),
            deepcopy(self.media_assets.items),
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_value
        del traceback

        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self._transaction_snapshot = None

    def commit(self) -> None:
        """Commit the in-memory transaction."""

        if self._transaction_snapshot is None:
            raise RuntimeError(
                "Fake Unit of Work is not active.",
            )

        self.commit_count += 1

    def rollback(self) -> None:
        """Restore repository state from the transaction snapshot."""

        if self._transaction_snapshot is None:
            raise RuntimeError(
                "Fake Unit of Work is not active.",
            )

        (
            profiles,
            snapshots,
            searches,
            candidates,
            score_snapshots,
            media_assets,
        ) = self._transaction_snapshot

        self.profiles.items = profiles
        self.snapshots.items = snapshots
        self.searches.items = searches
        self.candidates.items = candidates
        self.score_snapshots.items = score_snapshots
        self.media_assets.items = media_assets

        self.rollback_count += 1
