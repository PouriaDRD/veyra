"""Tests for database health checks."""

from pathlib import Path

from veyra.infrastructure.database import (
    check_database_health,
    create_database_engine,
)


def test_database_health_check_succeeds(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    try:
        health = check_database_health(engine)

        assert health.healthy is True
        assert health.sqlite_version is not None
    finally:
        engine.dispose()
