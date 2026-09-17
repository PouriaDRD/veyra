"""Tests for runtime directory preparation."""

from pathlib import Path

from veyra.config import Settings, prepare_runtime_directories


def test_prepare_runtime_directories(
    tmp_path: Path,
) -> None:
    settings = Settings(
        database_path=tmp_path / "database" / "veyra.db",
        media_root=tmp_path / "media",
        log_dir=tmp_path / "logs",
    )

    prepare_runtime_directories(settings)

    assert settings.database_path.parent.is_dir()
    assert settings.media_root.is_dir()
    assert settings.log_dir.is_dir()
