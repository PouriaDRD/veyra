"""Database health checks."""

from dataclasses import dataclass

from sqlalchemy import Engine, text


@dataclass(frozen=True, slots=True)
class DatabaseHealth:
    """Database health-check result."""

    healthy: bool
    sqlite_version: str | None = None


def check_database_health(
    engine: Engine,
) -> DatabaseHealth:
    """Verify database connectivity and return SQLite metadata."""

    try:
        with engine.connect() as connection:
            sqlite_version = connection.execute(
                text("SELECT sqlite_version()"),
            ).scalar_one()

        return DatabaseHealth(
            healthy=True,
            sqlite_version=str(sqlite_version),
        )
    except Exception:
        return DatabaseHealth(
            healthy=False,
        )
