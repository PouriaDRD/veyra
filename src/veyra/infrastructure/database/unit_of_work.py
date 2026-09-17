"""SQLAlchemy Unit of Work implementation."""

from types import TracebackType

from sqlalchemy.orm import Session

from .session import SessionFactory


class SqlAlchemyUnitOfWork:
    """
    Transaction boundary for application operations.

    A new SQLAlchemy session is created for each Unit of Work instance.
    Successful context-manager exits commit automatically, while failures
    roll back the transaction.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

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

        self._session = self._session_factory()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Commit a successful transaction or roll back a failed one.

        The session is always closed after transaction completion.
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
        """Commit the active transaction explicitly."""

        self.session.commit()

    def rollback(self) -> None:
        """Roll back the active transaction explicitly."""

        self.session.rollback()
