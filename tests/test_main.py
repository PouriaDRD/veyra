"""Tests for Veyra's executable entrypoint."""

from pathlib import Path

import pytest

from veyra.__main__ import main
from veyra.config import clear_settings_cache


def test_main_runs_application_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv(
        "VEYRA_ENV",
        "test",
    )

    monkeypatch.setenv(
        "VEYRA_DATABASE_PATH",
        str(tmp_path / "data" / "veyra.db"),
    )

    monkeypatch.setenv(
        "VEYRA_MEDIA_ROOT",
        str(tmp_path / "media"),
    )

    monkeypatch.setenv(
        "VEYRA_LOG_DIR",
        str(tmp_path / "logs"),
    )

    clear_settings_cache()

    try:
        main()
    finally:
        clear_settings_cache()

    assert (tmp_path / "logs" / "veyra.log").exists()
