"""SQLAlchemy Unit of Work implementation."""

from types import TracebackType

from sqlalchemy.orm import Session

from .repositories import (
    SqlAlchemyMediaAssetRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySearchCandidateRepository,
    SqlAlchemySearchRepository,
    SqlAlchemySnapshotRepository,
)
from .session import SessionFactory


class SqlAlchemyUnitOfWork:
    """
    SQLAlchemy-backed application transaction boundary.

    Repositories share the same session so all operations performed within
    one Unit of Work participate in the same database transaction.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

        self.profiles: SqlAlchemyProfileRepository
        self.snapshots: SqlAlchemySnapshotRepository
        self.searches: SqlAlchemySearchRepository
        self.candidates: SqlAlchemySearchCandidateRepository
        self.media_assets: SqlAlchemyMediaAssetRepository

    @property
    def session(self) -> Session:
        """
        Return the active SQLAlchemy session.

        Raises:
            RuntimeError: If the Unit of Work has not been entered.
        """

        if self._session is None:
            raise RuntimeError(
                "Unit of Work has not been started.",
            )

        return self._session

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        """Start a new transactional Unit of Work."""

        if self._session is not None:
            raise RuntimeError(
                "Unit of Work is already active.",
            )

        session = self._session_factory()

        self._session = session

        self.profiles = SqlAlchemyProfileRepository(
            session,
        )

        self.snapshots = SqlAlchemySnapshotRepository(
            session,
        )

        self.searches = SqlAlchemySearchRepository(
            session,
        )

        self.candidates = SqlAlchemySearchCandidateRepository(
            session,
        )

        self.media_assets = SqlAlchemyMediaAssetRepository(
            session,
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Commit successful work or roll back failed work.

        The active session is always closed afterward.
        """

        if self._session is None:
            return

        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        """Commit the active transaction."""

        self.session.commit()

    def rollback(self) -> None:
        """Roll back the active transaction."""

        self.session.rollback()
