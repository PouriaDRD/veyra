"""Tests for structured logging configuration."""

import json
from pathlib import Path

from veyra.config import Settings
from veyra.logging import configure_logging, get_logger


def test_configure_logging_creates_json_log_file(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "logs"

    settings = Settings(
        log_dir=log_dir,
        log_level="INFO",
    )

    configure_logging(settings)

    logger = get_logger("veyra.test")

    logger.info(
        "test_event",
        profile_id="profile-123",
    )

    log_file = log_dir / "veyra.log"

    assert log_file.exists()

    lines = log_file.read_text(
        encoding="utf-8",
    ).splitlines()

    assert lines

    event = json.loads(lines[-1])

    assert event["event"] == "test_event"
    assert event["profile_id"] == "profile-123"
    assert event["level"] == "info"
    assert event["logger"] == "veyra.test"
