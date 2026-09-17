"""Tests for the SQLAlchemy Unit of Work."""

from pathlib import Path

import pytest
from sqlalchemy import text

from veyra.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)


def test_unit_of_work_commits_successful_transaction(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    session_factory = create_session_factory(engine)

    try:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    CREATE TABLE test_records (
                        id INTEGER PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """),
            )

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.session.execute(
                text("""
                    INSERT INTO test_records (value)
                    VALUES (:value)
                    """),
                {
                    "value": "committed",
                },
            )

        with engine.connect() as connection:
            count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM test_records",
                ),
            ).scalar_one()

        assert count == 1
    finally:
        engine.dispose()


def test_unit_of_work_rolls_back_failed_transaction(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    session_factory = create_session_factory(engine)

    try:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    CREATE TABLE test_records (
                        id INTEGER PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """),
            )

        with (
            pytest.raises(
                RuntimeError,
                match="forced failure",
            ),
            SqlAlchemyUnitOfWork(session_factory) as unit_of_work,
        ):
            unit_of_work.session.execute(
                text("""
                    INSERT INTO test_records (value)
                    VALUES (:value)
                    """),
                {
                    "value": "rolled-back",
                },
            )

            raise RuntimeError(
                "forced failure",
            )

        with engine.connect() as connection:
            count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM test_records",
                ),
            ).scalar_one()

        assert count == 0
    finally:
        engine.dispose()
