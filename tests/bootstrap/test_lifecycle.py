"""Tests for the Veyra application lifecycle."""

from pathlib import Path

import pytest
import structlog

from veyra.bootstrap import ApplicationLifecycle
from veyra.config import AppEnvironment, Settings


def build_test_settings(
    tmp_path: Path,
) -> Settings:
    """Build isolated settings for lifecycle tests."""

    return Settings(
        environment=AppEnvironment.TEST,
        debug=False,
        database_path=tmp_path / "data" / "veyra.db",
        media_root=tmp_path / "media",
        log_dir=tmp_path / "logs",
    )


def test_lifecycle_starts_application(
    tmp_path: Path,
) -> None:
    lifecycle = ApplicationLifecycle(
        settings=build_test_settings(tmp_path),
    )

    context = lifecycle.start()

    assert lifecycle.is_started is True
    assert lifecycle.context is context

    assert context.settings.environment is AppEnvironment.TEST

    log_context = structlog.contextvars.get_contextvars()

    assert log_context["application"] == "veyra"
    assert log_context["environment"] == "test"

    assert context.database_engine is not None
    assert context.session_factory is not None
    assert context.settings.database_path.exists()

    lifecycle.stop()


def test_start_is_idempotent(
    tmp_path: Path,
) -> None:
    lifecycle = ApplicationLifecycle(
        settings=build_test_settings(tmp_path),
    )

    first_context = lifecycle.start()
    second_context = lifecycle.start()

    assert first_context is second_context

    lifecycle.stop()


def test_stop_is_idempotent(
    tmp_path: Path,
) -> None:
    lifecycle = ApplicationLifecycle(
        settings=build_test_settings(tmp_path),
    )

    lifecycle.start()

    lifecycle.stop()
    lifecycle.stop()

    assert lifecycle.is_started is False


def test_context_requires_started_application(
    tmp_path: Path,
) -> None:
    lifecycle = ApplicationLifecycle(
        settings=build_test_settings(tmp_path),
    )

    with pytest.raises(
        RuntimeError,
        match="Veyra application has not been started",
    ):
        _ = lifecycle.context


def test_context_manager_starts_and_stops_application(
    tmp_path: Path,
) -> None:
    lifecycle = ApplicationLifecycle(
        settings=build_test_settings(tmp_path),
    )

    with lifecycle as context:
        assert lifecycle.is_started is True
        assert lifecycle.context is context

    assert lifecycle.is_started is False

    assert structlog.contextvars.get_contextvars() == {}
