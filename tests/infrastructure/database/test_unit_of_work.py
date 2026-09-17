"""Tests for the SQLAlchemy Unit of Work."""

from pathlib import Path

import pytest
from sqlalchemy import text

from veyra.domain.profiles import Profile, SocialPlatform
from veyra.infrastructure.database import (
    Base,
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


def test_domain_repositories_share_one_transaction(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    Base.metadata.create_all(engine)

    session_factory = create_session_factory(engine)

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="rollback-test",
        username="rollback_test",
    )

    try:
        with (
            pytest.raises(
                RuntimeError,
                match="forced failure",
            ),
            SqlAlchemyUnitOfWork(session_factory) as unit_of_work,
        ):
            unit_of_work.profiles.add(profile)

            raise RuntimeError(
                "forced failure",
            )

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            stored = unit_of_work.profiles.get_by_id(
                profile.id,
            )

            assert stored is None
    finally:
        engine.dispose()
