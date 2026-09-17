"""Database engine construction and SQLite configuration."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event

SQLITE_PRAGMAS: Mapping[str, str] = {
    "foreign_keys": "ON",
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "busy_timeout": "5000",
}


def build_sqlite_url(database_path: Path) -> str:
    """Build a SQLAlchemy SQLite URL from a filesystem path."""

    resolved_path = database_path.resolve()

    return f"sqlite:///{resolved_path.as_posix()}"


def _configure_sqlite_connection(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    """Apply required SQLite pragmas to each new DBAPI connection."""

    cursor = dbapi_connection.cursor()

    try:
        for pragma, value in SQLITE_PRAGMAS.items():
            cursor.execute(
                f"PRAGMA {pragma}={value}",
            )
    finally:
        cursor.close()


def create_database_engine(
    database_path: Path,
    *,
    echo: bool = False,
) -> Engine:
    """
    Create the Veyra SQLite engine.

    The database parent directory is created before the first connection.
    """

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    engine = create_engine(
        build_sqlite_url(database_path),
        echo=echo,
        future=True,
    )

    event.listen(
        engine,
        "connect",
        _configure_sqlite_connection,
    )

    return engine
