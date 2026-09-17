"""Tests for Veyra persistence schema."""

from pathlib import Path

from sqlalchemy import inspect

from veyra.infrastructure.database import (
    Base,
    create_database_engine,
)


def test_core_tables_are_registered_and_created(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    try:
        Base.metadata.create_all(engine)

        inspector = inspect(engine)

        assert set(inspector.get_table_names()) == {
            "media_assets",
            "profile_snapshots",
            "profiles",
            "score_snapshots",
            "search_candidates",
            "searches",
        }
    finally:
        engine.dispose()
