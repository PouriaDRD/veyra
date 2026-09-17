"""Tests for SQLAlchemy repository implementations."""

from pathlib import Path

from sqlalchemy import Engine

from veyra.domain.media import MediaAsset, MediaKind
from veyra.domain.profiles import Profile, SocialPlatform
from veyra.domain.searches import Search, SearchCandidate, SearchStatus
from veyra.domain.snapshots import ProfileSnapshot
from veyra.infrastructure.database import (
    Base,
    SessionFactory,
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)


def build_database(
    tmp_path: Path,
) -> tuple[Engine, SessionFactory]:
    """Create an isolated database for repository tests."""

    engine = create_database_engine(
        tmp_path / "veyra.db",
    )

    Base.metadata.create_all(engine)

    return (
        engine,
        create_session_factory(engine),
    )


def test_profile_repository_round_trip(
    tmp_path: Path,
) -> None:
    engine, session_factory = build_database(tmp_path)

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123456",
        username="test_profile",
    )

    try:
        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.profiles.add(profile)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            stored = unit_of_work.profiles.get_by_id(
                profile.id,
            )

            assert stored == profile

            by_external_id = unit_of_work.profiles.get_by_external_identity(
                SocialPlatform.INSTAGRAM,
                "123456",
            )

            assert by_external_id == profile

            by_username = unit_of_work.profiles.get_by_username(
                SocialPlatform.INSTAGRAM,
                "@test_profile",
            )

            assert by_username == profile
    finally:
        engine.dispose()


def test_profile_repository_updates_profile(
    tmp_path: Path,
) -> None:
    engine, session_factory = build_database(tmp_path)

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123",
        username="old_name",
    )

    try:
        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.profiles.add(profile)

        profile.change_username(
            "new_name",
        )

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.profiles.update(profile)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            stored = unit_of_work.profiles.get_by_id(
                profile.id,
            )

            assert stored is not None
            assert stored.username == "new_name"
    finally:
        engine.dispose()


def test_snapshot_repository_lists_newest_first(
    tmp_path: Path,
) -> None:
    engine, session_factory = build_database(tmp_path)

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123",
        username="snapshot_test",
    )

    first = ProfileSnapshot(
        profile_id=profile.id,
        username=profile.username,
        followers_count=100,
    )

    second = ProfileSnapshot(
        profile_id=profile.id,
        username=profile.username,
        followers_count=200,
    )

    second.captured_at = second.captured_at.replace(
        microsecond=second.captured_at.microsecond + 1,
    )

    try:
        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.profiles.add(profile)
            unit_of_work.snapshots.add(first)
            unit_of_work.snapshots.add(second)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            snapshots = unit_of_work.snapshots.list_for_profile(
                profile.id,
            )

            assert len(snapshots) == 2
            assert snapshots[0].followers_count == 200
            assert snapshots[1].followers_count == 100
    finally:
        engine.dispose()


def test_search_and_candidate_repositories(
    tmp_path: Path,
) -> None:
    engine, session_factory = build_database(tmp_path)

    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123",
        username="candidate",
    )

    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    candidate = SearchCandidate(
        search_id=search.id,
        profile_id=profile.id,
        discovery_source="test",
    )

    snapshot = ProfileSnapshot(
        profile_id=profile.id,
        username=profile.username,
    )

    try:
        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.profiles.add(profile)
            unit_of_work.searches.add(search)

        search.transition_to(
            SearchStatus.DISCOVERING,
        )

        candidate.attach_snapshot(
            snapshot.id,
        )

        candidate.mark_analyzed()
        candidate.set_score(8.75)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.snapshots.add(snapshot)
            unit_of_work.searches.update(search)
            unit_of_work.candidates.add(candidate)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            stored_search = unit_of_work.searches.get_by_id(
                search.id,
            )

            stored_candidate = unit_of_work.candidates.get_by_search_and_profile(
                search.id,
                profile.id,
            )

            candidates = unit_of_work.candidates.list_for_search(
                search.id,
            )

            assert stored_search == search
            assert stored_candidate == candidate
            assert candidates == [candidate]
    finally:
        engine.dispose()


def test_media_repository_deduplication_lookup(
    tmp_path: Path,
) -> None:
    engine, session_factory = build_database(tmp_path)

    asset = MediaAsset(
        sha256="a" * 64,
        kind=MediaKind.IMAGE,
        mime_type="image/jpeg",
        extension="jpg",
        byte_size=1024,
        storage_path=Path(
            "data/media/aa/example.jpg",
        ),
        width=512,
        height=512,
    )

    try:
        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            unit_of_work.media_assets.add(asset)

        with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            by_hash = unit_of_work.media_assets.get_by_sha256(
                asset.sha256,
            )

            by_path = unit_of_work.media_assets.get_by_storage_path(
                str(asset.storage_path),
            )

            assert by_hash == asset
            assert by_path == asset
    finally:
        engine.dispose()
