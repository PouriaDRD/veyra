"""Tests for domain persistence mappers."""

from pathlib import Path
from uuid import uuid4

from veyra.domain.media import MediaAsset, MediaKind
from veyra.domain.profiles import Profile, SocialPlatform
from veyra.domain.searches import Search, SearchCandidate, SearchStatus
from veyra.domain.snapshots import ProfileSnapshot
from veyra.infrastructure.database.mappers import (
    candidate_to_domain,
    candidate_to_model,
    media_asset_to_domain,
    media_asset_to_model,
    profile_to_domain,
    profile_to_model,
    search_to_domain,
    search_to_model,
    snapshot_to_domain,
    snapshot_to_model,
)


def test_profile_mapper_round_trip() -> None:
    profile = Profile(
        platform=SocialPlatform.INSTAGRAM,
        external_id="123456",
        username="veyra_test",
    )

    reconstructed = profile_to_domain(
        profile_to_model(profile),
    )

    assert reconstructed == profile


def test_snapshot_mapper_round_trip() -> None:
    snapshot = ProfileSnapshot(
        profile_id=uuid4(),
        username="veyra_test",
        display_name="Veyra Test",
        bio="Test bio",
        followers_count=125,
        following_count=80,
        posts_count=12,
        is_private=False,
        is_verified=False,
    )

    reconstructed = snapshot_to_domain(
        snapshot_to_model(snapshot),
    )

    assert reconstructed == snapshot


def test_search_mapper_round_trip() -> None:
    search = Search(
        platform=SocialPlatform.INSTAGRAM,
    )

    search.transition_to(
        SearchStatus.DISCOVERING,
    )

    reconstructed = search_to_domain(
        search_to_model(search),
    )

    assert reconstructed == search


def test_candidate_mapper_round_trip() -> None:
    candidate = SearchCandidate(
        search_id=uuid4(),
        profile_id=uuid4(),
        discovery_source="test_provider",
    )

    candidate.attach_snapshot(
        uuid4(),
    )

    candidate.mark_analyzed()
    candidate.set_score(8.5)

    reconstructed = candidate_to_domain(
        candidate_to_model(candidate),
    )

    assert reconstructed == candidate


def test_media_mapper_round_trip() -> None:
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

    reconstructed = media_asset_to_domain(
        media_asset_to_model(asset),
    )

    assert reconstructed == asset
