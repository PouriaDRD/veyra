"""Tests for database engine configuration."""

from pathlib import Path

from sqlalchemy import text

from veyra.infrastructure.database import (
    build_sqlite_url,
    create_database_engine,
)


def test_build_sqlite_url_uses_absolute_path(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "veyra.db"

    url = build_sqlite_url(database_path)

    assert url.startswith("sqlite:///")
    assert database_path.resolve().as_posix() in url


def test_sqlite_engine_enables_required_pragmas(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    try:
        with engine.connect() as connection:
            foreign_keys = connection.execute(
                text("PRAGMA foreign_keys"),
            ).scalar_one()

            journal_mode = connection.execute(
                text("PRAGMA journal_mode"),
            ).scalar_one()

            synchronous = connection.execute(
                text("PRAGMA synchronous"),
            ).scalar_one()

            busy_timeout = connection.execute(
                text("PRAGMA busy_timeout"),
            ).scalar_one()

        assert foreign_keys == 1
        assert str(journal_mode).lower() == "wal"
        assert synchronous == 1
        assert busy_timeout == 5000
    finally:
        engine.dispose()
