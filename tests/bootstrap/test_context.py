"""Tests for the Veyra application context."""

from pathlib import Path

from veyra.bootstrap import ApplicationContext
from veyra.config import Settings
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

    context = ApplicationContext(
        settings=settings,
        logger=logger,
    )

    assert context.settings is settings
    assert context.logger is logger
