"""Tests for the Veyra application context."""

from pathlib import Path

from veyra.bootstrap import ApplicationContext
from veyra.config import Settings
from veyra.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from veyra.logging import configure_logging, get_logger


def test_application_context_holds_runtime_dependencies(
    tmp_path: Path,
) -> None:
    settings = Settings(
        database_path=tmp_path / "data" / "veyra.db",
        media_root=tmp_path / "media",
        log_dir=tmp_path / "logs",
    )

    configure_logging(settings)

    logger = get_logger("veyra.test")

    engine = create_database_engine(
        settings.database_path,
    )

    session_factory = create_session_factory(
        engine,
    )

    try:
        context = ApplicationContext(
            settings=settings,
            logger=logger,
            database_engine=engine,
            session_factory=session_factory,
        )

        assert context.settings is settings
        assert context.logger is logger
        assert context.database_engine is engine
        assert context.session_factory is session_factory
    finally:
        engine.dispose()
