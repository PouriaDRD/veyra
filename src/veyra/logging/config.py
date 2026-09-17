"""Structured logging configuration."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import cast

import structlog
from structlog.stdlib import BoundLogger

from veyra.config import Settings, prepare_runtime_directories

LOG_FILENAME = "veyra.log"


def _get_log_level(level: str) -> int:
    """Convert a textual log level to its standard logging value."""

    return logging.getLevelNamesMapping()[level]


def _build_shared_processors() -> list[structlog.types.Processor]:
    """Return processors shared by Structlog and standard-library logs."""

    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(
            fmt="iso",
            utc=True,
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _build_console_formatter(
    shared_processors: list[structlog.types.Processor],
) -> structlog.stdlib.ProcessorFormatter:
    """Build the human-readable development console formatter."""

    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(
                colors=sys.stderr.isatty(),
            ),
        ],
    )


def _build_json_formatter(
    shared_processors: list[structlog.types.Processor],
) -> structlog.stdlib.ProcessorFormatter:
    """Build the machine-readable JSON file formatter."""

    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )


def _create_console_handler(
    level: int,
    shared_processors: list[structlog.types.Processor],
) -> logging.Handler:
    """Create the console logging handler."""

    handler = logging.StreamHandler(
        stream=sys.stderr,
    )

    handler.setLevel(level)

    handler.setFormatter(
        _build_console_formatter(
            shared_processors,
        ),
    )

    return handler


def _create_file_handler(
    *,
    log_dir: Path,
    level: int,
    max_bytes: int,
    backup_count: int,
    shared_processors: list[structlog.types.Processor],
) -> logging.Handler:
    """Create the rotating structured JSON file handler."""

    handler = RotatingFileHandler(
        filename=log_dir / LOG_FILENAME,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    handler.setLevel(level)

    handler.setFormatter(
        _build_json_formatter(
            shared_processors,
        ),
    )

    return handler


def configure_logging(
    settings: Settings,
) -> None:
    """
    Configure Veyra's structured logging system.

    Console output is optimized for humans while persisted log files
    use newline-delimited JSON suitable for later querying and analysis.
    """

    prepare_runtime_directories(settings)

    log_level = _get_log_level(
        settings.log_level,
    )

    shared_processors = _build_shared_processors()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            log_level,
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    root_logger.addHandler(
        _create_console_handler(
            level=log_level,
            shared_processors=shared_processors,
        ),
    )

    root_logger.addHandler(
        _create_file_handler(
            log_dir=settings.log_dir,
            level=log_level,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
            shared_processors=shared_processors,
        ),
    )


def get_logger(
    name: str,
) -> BoundLogger:
    """Return a structured logger for the requested module."""

    return cast(
        BoundLogger,
        structlog.get_logger(name),
    )
