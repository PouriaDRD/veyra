"""Tests for application settings."""

from pathlib import Path

import pytest

from veyra.config import AppEnvironment, Settings


def test_default_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.environment is AppEnvironment.DEVELOPMENT
    assert settings.debug is True
    assert settings.log_level == "INFO"

    assert settings.database_path == Path("data/veyra.db")
    assert settings.media_root == Path("data/media")
    assert settings.log_dir == Path("logs")


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv(
        "VEYRA_ENV",
        "production",
    )
    monkeypatch.setenv(
        "VEYRA_DEBUG",
        "false",
    )
    monkeypatch.setenv(
        "VEYRA_LOG_LEVEL",
        "warning",
    )

    settings = Settings()

    assert settings.environment is AppEnvironment.PRODUCTION
    assert settings.debug is False
    assert settings.log_level == "WARNING"

    assert settings.is_production is True
    assert settings.is_development is False
    assert settings.is_test is False


def test_log_level_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv(
        "VEYRA_LOG_LEVEL",
        "  debug  ",
    )

    settings = Settings()

    assert settings.log_level == "DEBUG"


def test_environment_can_be_provided_directly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings(
        environment=AppEnvironment.TEST,
    )

    assert settings.environment is AppEnvironment.TEST
    assert settings.is_test is True
