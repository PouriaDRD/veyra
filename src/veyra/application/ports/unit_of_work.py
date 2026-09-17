"""Application Unit of Work contract."""

from types import TracebackType
from typing import Protocol, Self

from .repositories import (
    MediaAssetRepository,
    ProfileRepository,
    SearchCandidateRepository,
    SearchRepository,
    SnapshotRepository,
)


class UnitOfWork(Protocol):
    """
    Transaction boundary exposed to application services.

    Infrastructure implementations may use SQLAlchemy or another storage
    technology without affecting application code.
    """

    @property
    def profiles(self) -> ProfileRepository:
        """Return the profile repository."""
        ...

    @property
    def snapshots(self) -> SnapshotRepository:
        """Return the snapshot repository."""
        ...

    @property
    def searches(self) -> SearchRepository:
        """Return the search repository."""
        ...

    @property
    def candidates(self) -> SearchCandidateRepository:
        """Return the search-candidate repository."""
        ...

    @property
    def media_assets(self) -> MediaAssetRepository:
        """Return the media-asset repository."""
        ...

    def __enter__(self) -> Self:
        """Start the Unit of Work."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the Unit of Work."""
        ...

    def commit(self) -> None:
        """Commit the current transaction."""
        ...

    def rollback(self) -> None:
        """Roll back the current transaction."""
        ...
