"""Tests for database session configuration."""

from pathlib import Path

from sqlalchemy.orm import Session

from veyra.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def test_session_factory_creates_session(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    session_factory = create_session_factory(engine)

    try:
        session = session_factory()

        assert isinstance(session, Session)

        session.close()
    finally:
        engine.dispose()
