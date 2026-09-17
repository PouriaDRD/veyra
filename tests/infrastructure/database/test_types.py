"""Tests for custom SQLAlchemy database types."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import StatementError

from veyra.infrastructure.database import (
    ProfileModel,
    create_database_engine,
    create_session_factory,
)


def test_utc_datetime_survives_sqlite_round_trip(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    ProfileModel.metadata.create_all(engine)

    session_factory = create_session_factory(engine)

    source_timezone = timezone(
        timedelta(
            hours=3,
            minutes=30,
        )
    )

    source_datetime = datetime(
        2026,
        9,
        17,
        12,
        0,
        tzinfo=source_timezone,
    )

    try:
        with session_factory() as session:
            profile = ProfileModel(
                id=uuid4(),
                platform="instagram",
                external_id="123",
                username="test",
                created_at=source_datetime,
                updated_at=source_datetime,
            )

            session.add(profile)
            session.commit()

        with session_factory() as session:
            stored = session.execute(
                select(ProfileModel),
            ).scalar_one()

            assert stored.created_at.tzinfo is UTC
            assert stored.created_at.hour == 8
            assert stored.created_at.minute == 30
    finally:
        engine.dispose()


def test_utc_datetime_rejects_naive_value(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    ProfileModel.metadata.create_all(engine)

    session_factory = create_session_factory(engine)

    try:
        with (
            pytest.raises(
                StatementError,
                match="timezone-aware",
            ) as exc_info,
            session_factory() as session,
        ):
            profile = ProfileModel(
                id=uuid4(),
                platform="instagram",
                external_id="123",
                username="test",
                created_at=datetime(
                    2026,
                    9,
                    17,
                    12,
                    0,
                ),
                updated_at=datetime(
                    2026,
                    9,
                    17,
                    12,
                    0,
                ),
            )

            session.add(profile)
            session.commit()

        assert isinstance(
            exc_info.value.orig,
            ValueError,
        )
    finally:
        engine.dispose()
