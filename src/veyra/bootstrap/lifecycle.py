"""Veyra application lifecycle."""

from dataclasses import dataclass, field
from time import monotonic

from sqlalchemy import Engine

from veyra.config import Settings, get_settings
from veyra.infrastructure.database import (
    check_database_health,
    create_database_engine,
    create_session_factory,
)
from veyra.logging import (
    bind_log_context,
    clear_log_context,
    configure_logging,
    get_logger,
)

from .context import ApplicationContext

LOGGER_NAME = "veyra"


@dataclass(slots=True)
class ApplicationLifecycle:
    """
    Manage Veyra startup and shutdown.

    Lifecycle operations are intentionally explicit so future entrypoints
    such as ASGI applications, CLI commands, and workers can all share
    the same initialization flow.
    """

    settings: Settings | None = None

    _context: ApplicationContext | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _started_at: float | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _database_engine: Engine | None = field(
        default=None,
        init=False,
        repr=False,
    )

    @property
    def is_started(self) -> bool:
        """Return whether the application lifecycle is currently active."""

        return self._context is not None

    @property
    def context(self) -> ApplicationContext:
        """
        Return the active application context.

        Raises:
            RuntimeError: If the application has not been started.
        """

        if self._context is None:
            raise RuntimeError(
                "Veyra application has not been started.",
            )

        return self._context

    def start(self) -> ApplicationContext:
        """
        Start Veyra and return its application context.

        Startup is idempotent. Calling start more than once returns the
        existing active context instead of reconfiguring the application.
        """

        if self._context is not None:
            return self._context

        settings = self.settings or get_settings()

        configure_logging(settings)

        clear_log_context()

        bind_log_context(
            application="veyra",
            environment=settings.environment.value,
        )

        logger = get_logger(LOGGER_NAME)

        database_engine = create_database_engine(
            settings.database_path,
            echo=settings.database_echo,
        )

        session_factory = create_session_factory(
            database_engine,
        )

        database_health = check_database_health(
            database_engine,
        )

        if not database_health.healthy:
            database_engine.dispose()

            raise RuntimeError(
                "Veyra database health check failed.",
            )

        context = ApplicationContext(
            settings=settings,
            logger=logger,
            database_engine=database_engine,
            session_factory=session_factory,
        )

        self._database_engine = database_engine
        self._started_at = monotonic()
        self._context = context

        logger.info(
            "application_started",
            debug=settings.debug,
            sqlite_version=database_health.sqlite_version,
        )

        return context

    def stop(self) -> None:
        """
        Stop Veyra gracefully.

        Shutdown is idempotent so callers may safely invoke it even when
        startup failed or the lifecycle has already been stopped.
        """

        if self._context is None:
            return

        elapsed_seconds = self._get_elapsed_seconds()

        self._context.logger.info(
            "application_stopped",
            uptime_seconds=elapsed_seconds,
        )

        if self._database_engine is not None:
            self._database_engine.dispose()

        self._context = None
        self._database_engine = None
        self._started_at = None

        clear_log_context()

    def _get_elapsed_seconds(self) -> float:
        """Return application uptime in seconds."""

        if self._started_at is None:
            return 0.0

        return round(
            monotonic() - self._started_at,
            6,
        )

    def __enter__(self) -> ApplicationContext:
        """Start the application when entering a context manager."""

        return self.start()

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        """Stop the application when leaving a context manager."""

        self.stop()
